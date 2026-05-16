# coding: utf-8
from enum import Enum

from PyQt5.QtCore import Qt, QObject, pyqtProperty, QPropertyAnimation, QEasingCurve, QPointF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QCheckBox, QStyle, QStyleOptionButton, QWidget

from ...common.style_sheet import FluentStyleSheet, isDarkTheme, ThemeColor, setCustomStyleSheet
from ...common.overload import singledispatchmethod
from ...common.color import fallbackThemeColor, validColor
from ...common.font import setFont


class CheckBoxState(Enum):
    """ Check box state """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    CHECKED = 3
    CHECKED_HOVER = 4
    CHECKED_PRESSED = 5
    DISABLED = 6
    CHECKED_DISABLED = 7


class _CheckBoxIndicatorAnimation(QObject):
    """ CheckBox indicator animation """

    checkInCurve = QEasingCurve(QEasingCurve.Type.BezierSpline)
    checkInCurve.addCubicBezierSegment(QPointF(0.55, 0), QPointF(0, 1), QPointF(1, 1))
    checkOutCurve = QEasingCurve(QEasingCurve.Type.BezierSpline)
    checkOutCurve.addCubicBezierSegment(QPointF(0.167, 0.167), QPointF(0.833, 0.833), QPointF(1, 1))

    def __init__(self, updateCallback, parent=None):
        super().__init__(parent)
        self.previousState = Qt.Unchecked
        self.currentState = Qt.Unchecked
        self._progress = 1
        self._updateCallback = updateCallback
        self.ani = QPropertyAnimation(self, b'progress', self)

    def start(self, previousState, currentState):
        self.previousState = previousState
        self.currentState = currentState
        self.ani.stop()

        if previousState == Qt.Unchecked and currentState == Qt.Checked:
            self._startAnimation(317)
        elif previousState == Qt.Checked and currentState == Qt.Unchecked:
            self._startAnimation(67)
        else:
            self.progress = 1

    def _startAnimation(self, duration):
        self.ani.setDuration(duration)
        self.ani.setStartValue(0)
        self.ani.setEndValue(1)
        self.ani.setEasingCurve(QEasingCurve.Linear)
        self.ani.start()

    def value(self):
        return self._progress

    def setValue(self, progress):
        self._progress = progress
        self._updateCallback()

    progress = pyqtProperty(float, value, setValue)


def _checkBoxIconColor():
    return QColor(Qt.black if isDarkTheme() else Qt.white)


def _mapCheckPoint(rect, point):
    return QPointF(rect.x() + point.x() * rect.width() / 48, rect.y() + point.y() * rect.height() / 48)


def _drawPolyline(painter, rect, points, start=0, end=1):
    if start >= end:
        return

    mapped = [_mapCheckPoint(rect, p) for p in points]
    lens = [((mapped[i].x() - mapped[i - 1].x()) ** 2 + (mapped[i].y() - mapped[i - 1].y()) ** 2) ** 0.5
            for i in range(1, len(mapped))]
    total = sum(lens)
    path = QPainterPath()

    for i, length in enumerate(lens):
        a = sum(lens[:i]) / total
        b = (sum(lens[:i]) + length) / total
        if end <= a or start >= b:
            continue

        p1, p2 = mapped[i], mapped[i + 1]
        s = max(start, a)
        e = min(end, b)
        sp = p1 + (p2 - p1) * ((s - a) / (b - a))
        ep = p1 + (p2 - p1) * ((e - a) / (b - a))
        path.moveTo(sp)
        path.lineTo(ep)

    painter.drawPath(path)


def _drawCheckBoxIndicator(painter, rect, checkState, borderColor, backgroundColor,
                           foregroundColor=None, progress=1, previousState=None, glyphOpacity=1):
    """ draw CheckBox indicator """
    painter.save()
    painter.setPen(borderColor)
    painter.setBrush(backgroundColor)
    painter.drawRoundedRect(rect, 4.5, 4.5)

    if checkState == Qt.Unchecked and not (previousState == Qt.Checked and progress < 1):
        painter.restore()
        return

    painter.setOpacity(glyphOpacity)
    pen = QPen(foregroundColor or _checkBoxIconColor(), max(1.4, rect.width() / 12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if checkState == Qt.PartiallyChecked:
        _drawPolyline(painter, rect, [QPointF(15.775, 23.912), QPointF(32.3125, 23.912)])
    elif checkState == Qt.Checked:
        p = _CheckBoxIndicatorAnimation.checkInCurve.valueForProgress(progress) if previousState == Qt.Unchecked else 1
        _drawPolyline(painter, rect, [QPointF(13.3796, 23.0112), QPointF(20.5, 30.1316), QPointF(34.7359, 15.7641)], end=p)
    else:
        p = _CheckBoxIndicatorAnimation.checkOutCurve.valueForProgress(progress)
        _drawPolyline(painter, rect, [QPointF(13.3796, 23.0112), QPointF(20.5, 30.1316), QPointF(34.7359, 15.7641)], start=p)

    painter.restore()


def _itemCheckBoxAnimation(delegate, index, option, checkState):
    key = (id(index.model()), index.internalId(), index.row(), index.column())
    delegate._checkBoxRects[key] = option.rect
    ani = delegate._checkBoxAnis.get(key)

    if ani is None:
        ani = _CheckBoxIndicatorAnimation(lambda k=key: _updateItemCheckBox(delegate, k), delegate)
        delegate._checkBoxAnis[key] = ani

    previousState = delegate._checkBoxStates.get(key, checkState)
    if previousState != checkState:
        ani.start(previousState, checkState)
        delegate._checkBoxStates[key] = checkState

    return ani


def _updateItemCheckBox(delegate, key):
    rect = delegate._checkBoxRects.get(key)
    delegate.parent().viewport().update(rect.adjusted(-2, -2, 2, 2) if rect else delegate.parent().viewport().rect())


class CheckBox(QCheckBox):
    """ Check box

    Constructors
    ------------
    * CheckBox(`parent`: QWidget = None)
    * CheckBox(`text`: str, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        setFont(self)
        FluentStyleSheet.CHECK_BOX.apply(self)
        self.isPressed = False
        self.isHover = False
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()
        self.lightTextColor = QColor(0, 0, 0)
        self.darkTextColor = QColor(255, 255, 255)

        self._states = {}
        self._checkState = self.checkState()
        self._indicatorAni = _CheckBoxIndicatorAnimation(self.update, self)
        self.stateChanged.connect(self._startIndicatorAnimation)

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def setCheckedColor(self, light, dark):
        """ set the color of indicator in checked status

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            indicator color in light/dark theme mode
        """
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.update()

    def setTextColor(self, light, dark):
        """ set the color of text

        Parameters
        ----------
        light, dark: str | QColor | Qt.GlobalColor
            text color in light/dark theme mode
        """
        self.lightTextColor = QColor(light)
        self.darkTextColor = QColor(dark)

        setCustomStyleSheet(
            self,
            f"CheckBox{{color:{self.lightTextColor.name(QColor.NameFormat.HexArgb)}}}",
            f"CheckBox{{color:{self.darkTextColor.name(QColor.NameFormat.HexArgb)}}}"
        )

    def _startIndicatorAnimation(self, state):
        state = Qt.CheckState(state)
        self._indicatorAni.start(self._checkState, state)
        self._checkState = state

    def _borderColor(self):
        if isDarkTheme():
            map = {
                CheckBoxState.NORMAL: QColor(255, 255, 255, 141),
                CheckBoxState.HOVER: QColor(255, 255, 255, 141),
                CheckBoxState.PRESSED: QColor(255, 255, 255, 40),
                CheckBoxState.CHECKED : fallbackThemeColor(self.darkCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.darkCheckedColor, ThemeColor.DARK_1.color()),
                CheckBoxState.CHECKED_PRESSED : validColor(self.darkCheckedColor, ThemeColor.DARK_2.color()),
                CheckBoxState.DISABLED : QColor(255, 255, 255, 41),
                CheckBoxState.CHECKED_DISABLED : QColor(0, 0, 0, 0)
            }
        else:
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 122),
                CheckBoxState.HOVER: QColor(0, 0, 0, 143),
                CheckBoxState.PRESSED: QColor(0, 0, 0, 69),
                CheckBoxState.CHECKED : fallbackThemeColor(self.lightCheckedColor),
                CheckBoxState.CHECKED_HOVER : validColor(self.lightCheckedColor, ThemeColor.LIGHT_1.color()),
                CheckBoxState.CHECKED_PRESSED : validColor(self.lightCheckedColor, ThemeColor.LIGHT_2.color()),
                CheckBoxState.DISABLED : QColor(0, 0, 0, 56),
                CheckBoxState.CHECKED_DISABLED : QColor(0, 0, 0, 0)
            }

        return map[self._state()]

    def _backgroundColor(self):
        if isDarkTheme():
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 26),
                CheckBoxState.HOVER: QColor(255, 255, 255, 11),
                CheckBoxState.PRESSED: QColor(255, 255, 255, 18),
                CheckBoxState.CHECKED: fallbackThemeColor(self.darkCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.darkCheckedColor, ThemeColor.DARK_1.color()),
                CheckBoxState.CHECKED_PRESSED: validColor(self.darkCheckedColor, ThemeColor.DARK_2.color()),
                CheckBoxState.DISABLED: QColor(0, 0, 0, 0),
                CheckBoxState.CHECKED_DISABLED: QColor(255, 255, 255, 41)
            }
        else:
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 6),
                CheckBoxState.HOVER: QColor(0, 0, 0, 13),
                CheckBoxState.PRESSED: QColor(0, 0, 0, 31),
                CheckBoxState.CHECKED: fallbackThemeColor(self.lightCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.lightCheckedColor, ThemeColor.LIGHT_1.color()),
                CheckBoxState.CHECKED_PRESSED: validColor(self.lightCheckedColor, ThemeColor.LIGHT_2.color()),
                CheckBoxState.DISABLED: QColor(0, 0, 0, 0),
                CheckBoxState.CHECKED_DISABLED: QColor(0, 0, 0, 56)
            }

        return map[self._state()]

    def _state(self):
        if not self.isEnabled():
            return CheckBoxState.CHECKED_DISABLED if self.isChecked() else CheckBoxState.DISABLED

        if self.isChecked():
            if self.isPressed:
                return CheckBoxState.CHECKED_PRESSED
            if self.isHover:
                return CheckBoxState.CHECKED_HOVER

            return CheckBoxState.CHECKED
        else:
            if self.isPressed:
                return CheckBoxState.PRESSED
            if self.isHover:
                return CheckBoxState.HOVER

            return CheckBoxState.NORMAL

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        # get the rect of indicator
        opt = QStyleOptionButton()
        opt.initFrom(self)
        rect = self.style().subElementRect(QStyle.SE_CheckBoxIndicator, opt, self)

        _drawCheckBoxIndicator(
            painter, rect, self.checkState(), self._borderColor(), self._backgroundColor(),
            progress=self._indicatorAni.progress, previousState=self._indicatorAni.previousState,
            glyphOpacity=0.8 if not self.isEnabled() else 1
        )
