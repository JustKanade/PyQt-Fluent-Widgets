# coding:utf-8
from typing import List, Union

from PyQt5.QtCore import (QEasingCurve, QElapsedTimer, QEvent, QPointF, QRect, QRectF, QSize, Qt,
                          QTimer, QVariantAnimation, pyqtSignal)
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QWidget

from ...common.config import qconfig
from ...common.font import getFont, setFont
from ...common.icon import FluentIcon, drawIcon
from ...common.style_sheet import isDarkTheme


ImageSource = Union[str, QImage, QPixmap]


class StoreCarouselItem:
    """ Store carousel item """

    def __init__(self, image: ImageSource, title: str = "", description: str = "", parameter=None,
                 actionButtonText: str = "See details", showActionButton: bool = True):
        self.image = image
        self.title = title
        self.description = description
        self.parameter = parameter
        self.actionButtonText = actionButtonText
        self.showActionButton = showActionButton

    @property
    def imageSource(self):
        return self.image if isinstance(self.image, str) else ""


class StoreCarouselEvent:
    """ Store carousel event data """

    def __init__(self, title: str = "", description: str = "", imageSource: str = "",
                 isThumbnail: bool = False, parameter=None, index: int = -1):
        self.title = title
        self.description = description
        self.imageSource = imageSource
        self.isThumbnail = isThumbnail
        self.parameter = parameter
        self.index = index


class StoreCarousel(QWidget):
    """ Store carousel """

    currentIndexChanged = pyqtSignal(int)
    itemClicked = pyqtSignal(StoreCarouselEvent)
    actionButtonClicked = pyqtSignal(StoreCarouselEvent)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._items = []  # type: List[StoreCarouselItem]
        self._thumbnailImages = [None, None, None]
        self._currentIndex = -1
        self._previousIndex = -1
        self._direction = 1
        self._progress = 1.0
        self._elapsed = 0
        self._autoShuffle = True
        self._shuffleDuration = 5000
        self._transitionDuration = 700
        self._pipsPagerVisible = True
        self._useImageEdgeOverContentColor = False
        self._borderRadius = 8
        self._isHover = False
        self._hoverPart = ""
        self._pressedPart = ""
        self._pixmaps = {}
        self._scaledPixmaps = {}
        self._colors = {}
        self._rects = {}
        self._pipRects = []
        self._thumbHits = []

        self._ani = QVariantAnimation(self)
        self._ani.setStartValue(0.0)
        self._ani.setEndValue(1.0)
        self._ani.setDuration(self._transitionDuration)
        self._ani.setEasingCurve(QEasingCurve.OutCubic)
        self._ani.valueChanged.connect(self._onAniValueChanged)

        self._clock = QElapsedTimer()
        self._tickTimer = QTimer(self)
        self._tickTimer.setInterval(33)
        self._tickTimer.timeout.connect(self._onTick)
        self._tickTimer.start()
        self._clock.start()

        setFont(self)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(520, 220)
        qconfig.themeChanged.connect(lambda _: self.update())

    def sizeHint(self):
        return QSize(735, 285)

    def setItems(self, items: List[StoreCarouselItem]):
        """ set carousel items """
        self._items = list(items or [])
        self._currentIndex = 0 if self._items else -1
        self._previousIndex = -1
        self._progress = 1.0
        self._elapsed = 0
        self._clearCache()
        self.currentIndexChanged.emit(self._currentIndex)
        self.update()

    def items(self):
        return self._items

    def addItem(self, item: StoreCarouselItem):
        """ add carousel item """
        self._items.append(item)
        if self._currentIndex < 0:
            self._currentIndex = 0
            self.currentIndexChanged.emit(0)
        self.update()

    def clear(self):
        self.setItems([])

    def setThumbnailImages(self, primary: ImageSource = None, secondary: ImageSource = None, tertiary: ImageSource = None):
        """ set thumbnail images """
        self._thumbnailImages = [primary, secondary, tertiary]
        self.update()

    def thumbnailImages(self):
        return self._thumbnailImages

    def goToNext(self):
        if self.count() > 0:
            self.goToIndex((self._currentIndex + 1) % self.count(), 1)

    def goToPrevious(self):
        if self.count() > 0:
            self.goToIndex((self._currentIndex - 1) % self.count(), -1)

    def goToIndex(self, index: int, direction: int = None):
        """ go to specified item """
        if not 0 <= index < self.count() or index == self._currentIndex:
            return

        self._previousIndex = self._currentIndex
        self._currentIndex = index
        self._direction = direction or (1 if index > self._previousIndex else -1)
        self._elapsed = 0
        self._ani.stop()
        self._ani.setDuration(self._transitionDuration)
        self._ani.start()
        self.currentIndexChanged.emit(index)
        self.update()

    def setCurrentIndex(self, index: int):
        self.goToIndex(index)

    def currentIndex(self):
        return self._currentIndex

    def currentItem(self):
        return self._items[self._currentIndex] if 0 <= self._currentIndex < self.count() else None

    def count(self):
        return len(self._items)

    def setAutoShuffle(self, enable: bool):
        self._autoShuffle = bool(enable)
        self._elapsed = 0
        self._clock.restart()
        self.update()

    def isAutoShuffle(self):
        return self._autoShuffle

    def setShuffleDuration(self, msec: int):
        self._shuffleDuration = max(1000, int(msec))
        self._elapsed = min(self._elapsed, self._shuffleDuration)
        self.update()

    def shuffleDuration(self):
        return self._shuffleDuration

    def setTransitionDuration(self, msec: int):
        self._transitionDuration = max(1, int(msec))
        self._ani.setDuration(self._transitionDuration)

    def transitionDuration(self):
        return self._transitionDuration

    def setPipsPagerVisible(self, visible: bool):
        self._pipsPagerVisible = bool(visible)
        self.update()

    def isPipsPagerVisible(self):
        return self._pipsPagerVisible

    def setUseImageEdgeOverContentColor(self, enable: bool):
        self._useImageEdgeOverContentColor = bool(enable)
        self._colors.clear()
        self.update()

    def useImageEdgeOverContentColor(self):
        return self._useImageEdgeOverContentColor

    def setBorderRadius(self, radius: int):
        self._borderRadius = max(0, int(radius))
        self.update()

    def borderRadius(self):
        return self._borderRadius

    def _onAniValueChanged(self, value):
        self._progress = float(value)
        self.update()

    def _onTick(self):
        dt = self._clock.restart()
        if not self._autoShuffle or self._isHover or self.count() < 2:
            return

        self._elapsed += min(dt, 100)
        if self._elapsed >= self._shuffleDuration:
            self._elapsed = 0
            self.goToNext()
        else:
            self.update(self._rects.get("arc", self.rect()))

    def _clearCache(self):
        self._pixmaps.clear()
        self._scaledPixmaps.clear()
        self._colors.clear()

    def _sourceKey(self, source: ImageSource):
        return source if isinstance(source, str) else id(source)

    def _sourceText(self, source: ImageSource):
        return source if isinstance(source, str) else ""

    def _pixmap(self, source: ImageSource):
        key = self._sourceKey(source)
        if key in self._pixmaps:
            return self._pixmaps[key]

        if isinstance(source, QPixmap):
            pixmap = source
        elif isinstance(source, QImage):
            pixmap = QPixmap.fromImage(source)
        elif source:
            pixmap = QPixmap(source)
        else:
            pixmap = QPixmap()

        self._pixmaps[key] = pixmap
        return pixmap

    def _coverPixmap(self, source: ImageSource, size: QSize):
        if size.isEmpty():
            return QPixmap()

        r = self.devicePixelRatioF()
        key = (self._sourceKey(source), size.width(), size.height(), round(r, 2))
        if key in self._scaledPixmaps:
            return self._scaledPixmaps[key]

        pixmap = self._pixmap(source)
        if pixmap.isNull():
            return pixmap

        target = QSize(max(1, int(size.width()*r)), max(1, int(size.height()*r)))
        scaled = pixmap.scaled(target, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = max(0, int((scaled.width() - target.width()) / 2))
        y = max(0, int((scaled.height() - target.height()) / 2))
        cropped = scaled.copy(x, y, target.width(), target.height())
        cropped.setDevicePixelRatio(r)
        self._scaledPixmaps[key] = cropped
        return cropped

    def _imageColor(self, source: ImageSource):
        key = (self._sourceKey(source), self._useImageEdgeOverContentColor)
        if key in self._colors:
            return self._colors[key]

        image = self._pixmap(source).toImage()
        if image.isNull():
            color = QColor(24, 24, 24)
        else:
            image = image.scaled(24, 24, Qt.IgnoreAspectRatio, Qt.FastTransformation).convertToFormat(QImage.Format_RGB32)
            pixels = []
            for y in range(image.height()):
                for x in range(image.width()):
                    if not self._useImageEdgeOverContentColor or x in (0, 23) or y in (0, 23):
                        pixels.append(QColor(image.pixel(x, y)))

            r = sum(c.red() for c in pixels) // len(pixels)
            g = sum(c.green() for c in pixels) // len(pixels)
            b = sum(c.blue() for c in pixels) // len(pixels)
            color = QColor(r, g, b)
            h, s, v, a = color.getHsvF()
            color = QColor.fromHsvF(h, min(s*1.15, 1), min(v*0.75, 1), a)

        self._colors[key] = color
        return color

    def _darker(self, color: QColor, factor=0.55, alpha=230):
        return QColor(int(color.red()*factor), int(color.green()*factor), int(color.blue()*factor), alpha)

    def _layoutRects(self):
        spacing = 15
        pipsH = 31 if self._pipsPagerVisible and self.count() > 1 else 0
        r = self.rect()

        if self.width() >= 1000:
            topH = max(0, r.height() - pipsH)
            leftW = int((r.width() - spacing) * 1.6 / 2.6)
            main = QRect(0, 0, leftW, topH)
            thumbs = QRect(leftW + spacing, 0, r.width() - leftW - spacing, topH)
            pips = QRect(0, topH - 10, leftW, pipsH)
        else:
            mainW = min(442, max(260, int((r.width() - spacing) * 0.615)))
            mainH = max(120, r.height() - pipsH - 6)
            main = QRect(0, 0, mainW, mainH)
            thumbs = QRect(mainW + spacing, 0, max(0, r.width() - mainW - spacing), mainH)
            pips = QRect(0, mainH, mainW, pipsH)

        return main, pips, thumbs

    def _paintCover(self, painter: QPainter, source: ImageSource, rect: QRect, radius=None, opacity=1, offset=0):
        if rect.isEmpty():
            return

        painter.save()
        painter.setOpacity(opacity)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius if radius is not None else self._borderRadius,
                            radius if radius is not None else self._borderRadius)
        painter.setClipPath(path)
        painter.drawPixmap(rect.topLeft() + QPointF(offset, 0).toPoint(), self._coverPixmap(source, rect.size()))
        painter.restore()

    def _drawShadow(self, painter: QPainter, rect: QRect, color: QColor, radius: int):
        painter.save()
        for i, a in enumerate((38, 22, 10), 1):
            c = QColor(color)
            c.setAlpha(a)
            painter.setPen(Qt.NoPen)
            painter.setBrush(c)
            painter.drawRoundedRect(rect.adjusted(-i*3, -i, i*3, i*3), radius + i*2, radius + i*2)
        painter.restore()

    def _drawButton(self, painter: QPainter, rect: QRect, icon: FluentIcon, color: QColor, part: str):
        if not self._isHover or self.count() < 2:
            return

        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        bg = self._darker(color, 0.5, 230 if part != self._pressedPart else 255)
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1))
        painter.setBrush(bg)
        painter.drawEllipse(rect)
        drawIcon(icon, painter, QRectF(rect).adjusted(11, 11, -11, -11), fill="#FFFFFF")
        painter.restore()

    def _drawPips(self, painter: QPainter, rect: QRect):
        self._pipRects = []
        if not self._pipsPagerVisible or self.count() < 2 or rect.height() <= 0:
            return

        n, d, gap = self.count(), 11, 1
        x = rect.center().x() - (n*d + (n - 1)*gap)/2
        y = rect.top() + 10
        dark = isDarkTheme()
        for i in range(n):
            pr = QRect(int(x + i*(d + gap)), int(y), d, d)
            self._pipRects.append(pr)
            isCurrent = i == self._currentIndex
            isHover = self._hoverPart == f"pip:{i}"
            alpha = 185 if (isCurrent or isHover) else 130
            color = QColor(255, 255, 255, alpha) if dark else QColor(0, 0, 0, alpha - 30)
            rr = 3 if (isCurrent or isHover) else 2.2
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QRectF(pr.center().x() - rr, pr.center().y() - rr, 2*rr, 2*rr))

    def _drawArc(self, painter: QPainter, rect: QRect):
        if not self._autoShuffle or self.count() < 2:
            return

        percent = max(0.0, 1 - self._elapsed / max(1, self._shuffleDuration))
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255, 190), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(QRectF(rect).adjusted(3, 3, -3, -3), 90*16, int(-360*16*percent))
        painter.restore()

    def _drawTextPanel(self, painter: QPainter, rect: QRect, color: QColor):
        item = self.currentItem()
        if not item:
            return

        p = self._progress
        x = rect.left() + max(42, int(rect.width()*0.225)) + (1 - p) * 100
        maxW = max(120, min(300, rect.width() - 80))
        y = rect.center().y() - 45
        scale = 0.8 + 0.2 * p

        painter.save()
        painter.setOpacity(p)
        painter.translate(x, y)
        painter.scale(scale, scale)
        painter.setPen(Qt.white)

        titleFont = getFont(24, QFont.DemiBold)
        bodyFont = getFont(13, QFont.DemiBold)
        titleRect = QFontMetrics(titleFont).boundingRect(QRect(0, 0, maxW, 120), Qt.TextWordWrap, item.title)
        painter.setFont(titleFont)
        painter.drawText(QRect(0, 0, maxW, titleRect.height() + 4), Qt.TextWordWrap, item.title)

        descY = titleRect.height() + 4
        painter.setFont(bodyFont)
        painter.setPen(QColor(255, 255, 255, 150))
        painter.drawText(QRect(0, descY, min(240, maxW), 56), Qt.TextWordWrap, item.description)

        self._rects["action"] = QRect()
        if item.showActionButton:
            br = QRect(0, descY + 34, max(110, QFontMetrics(bodyFont).horizontalAdvance(item.actionButtonText) + 30), 29)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._darker(color, 0.38, 210 if self._pressedPart != "action" else 245))
            painter.drawRoundedRect(br, 6, 6)
            painter.setPen(QColor(255, 255, 255, 150))
            painter.drawText(br, Qt.AlignCenter, item.actionButtonText)
            self._rects["action"] = QRect(int(x + br.x()*scale), int(y + br.y()*scale),
                                          int(br.width()*scale), int(br.height()*scale))

        painter.restore()

    def _drawThumbnails(self, painter: QPainter, grid: QRect):
        self._thumbHits = []
        if grid.isEmpty():
            return

        s = 15
        images = self._thumbnailImages
        if not any(images):
            images = [self._items[(self._currentIndex + i + 1) % self.count()].image if self.count() else None for i in range(3)]

        if self.width() >= 1000:
            h = (grid.height() - s) // 2
            rects = [
                QRect(grid.left(), grid.top(), grid.width(), h),
                QRect(grid.left(), grid.top() + h + s, (grid.width() - s) // 2, h),
                QRect(grid.left() + (grid.width() + s) // 2, grid.top() + h + s, (grid.width() - s) // 2, h),
            ]
        else:
            topH = max(0, int(grid.height()*0.63))
            smallH = max(0, grid.height() - topH - s)
            smallW = (grid.width() - s) // 2
            rects = [
                QRect(grid.left(), grid.top(), grid.width(), topH),
                QRect(grid.left(), grid.top() + topH + s, smallW, smallH),
                QRect(grid.left() + smallW + s, grid.top() + topH + s, grid.width() - smallW - s, smallH),
            ]

        for i, (source, rect) in enumerate(zip(images, rects)):
            if not source:
                continue
            color = self._imageColor(source)
            self._drawShadow(painter, rect, color, self._borderRadius)
            self._paintCover(painter, source, rect, self._borderRadius)
            self._thumbHits.append((rect, source, i))

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        mainRect, pipsRect, thumbGrid = self._layoutRects()
        self._rects = {"main": mainRect, "pips": pipsRect, "arc": QRect(mainRect.left() + 10, mainRect.bottom() - 30, 20, 20)}

        if self.count() < 1:
            return

        item = self.currentItem()
        color = self._imageColor(item.image)
        self._drawShadow(painter, mainRect, color, self._borderRadius)

        if 0 <= self._previousIndex < self.count() and self._progress < 1:
            self._paintCover(painter, self._items[self._previousIndex].image, mainRect, self._borderRadius, 1 - self._progress)
            self._paintCover(painter, item.image, mainRect, self._borderRadius, 1, self._direction*(1 - self._progress)*mainRect.width())
        else:
            self._paintCover(painter, item.image, mainRect, self._borderRadius)

        fade = QColor(color)
        fade.setAlpha(118)
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(QRectF(mainRect), self._borderRadius, self._borderRadius)
        painter.setClipPath(path)
        painter.setBrush(fade)
        painter.drawRect(QRect(mainRect.left(), mainRect.top(), int(mainRect.width()*0.4), mainRect.height()))
        painter.setClipping(False)

        self._drawButton(painter, QRect(mainRect.left() - 10, mainRect.center().y() - 16, 32, 32),
                         FluentIcon.CARE_LEFT_SOLID, color, "previous")
        self._drawButton(painter, QRect(mainRect.right() - 21, mainRect.center().y() - 16, 32, 32),
                         FluentIcon.CARE_RIGHT_SOLID, color, "next")
        self._rects["previous"] = QRect(mainRect.left() - 10, mainRect.center().y() - 16, 32, 32)
        self._rects["next"] = QRect(mainRect.right() - 21, mainRect.center().y() - 16, 32, 32)

        self._drawTextPanel(painter, mainRect, color)
        self._drawArc(painter, self._rects["arc"])
        self._drawPips(painter, pipsRect)
        self._drawThumbnails(painter, thumbGrid)

    def _hitPart(self, pos):
        for name in ("action", "previous", "next"):
            if self._rects.get(name, QRect()).contains(pos):
                return name

        for i, rect in enumerate(self._pipRects):
            if rect.contains(pos):
                return f"pip:{i}"

        for i, (rect, _, _) in enumerate(self._thumbHits):
            if rect.contains(pos):
                return f"thumb:{i}"

        return "main" if self._rects.get("main", QRect()).contains(pos) else ""

    def _event(self, item: StoreCarouselItem, isThumbnail=False, index=None, imageSource=None):
        return StoreCarouselEvent(
            item.title if item and not isThumbnail else "",
            item.description if item and not isThumbnail else "",
            imageSource if imageSource is not None else (item.imageSource if item else ""),
            isThumbnail,
            item.parameter if item and not isThumbnail else None,
            self._currentIndex if index is None else index,
        )

    def mouseMoveEvent(self, e):
        part = self._hitPart(e.pos())
        if part != self._hoverPart:
            self._hoverPart = part
            self.setCursor(Qt.PointingHandCursor if part else Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressedPart = self._hitPart(e.pos())
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return super().mouseReleaseEvent(e)

        part = self._hitPart(e.pos())
        item = self.currentItem()
        if part == self._pressedPart:
            if part == "next":
                self.goToNext()
            elif part == "previous":
                self.goToPrevious()
            elif part == "action" and item:
                self.actionButtonClicked.emit(self._event(item))
            elif part.startswith("pip:"):
                self.goToIndex(int(part.split(":")[1]))
            elif part.startswith("thumb:"):
                i = int(part.split(":")[1])
                _, source, index = self._thumbHits[i]
                self.itemClicked.emit(self._event(item, True, index, self._sourceText(source)))
            elif part == "main" and item:
                self.itemClicked.emit(self._event(item))

        self._pressedPart = ""
        self.update()
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self._isHover = True
        self._clock.restart()
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._isHover = False
        self._hoverPart = ""
        self._pressedPart = ""
        self.setCursor(Qt.ArrowCursor)
        self._clock.restart()
        self.update()
        super().leaveEvent(e)

    def wheelEvent(self, e):
        if e.angleDelta().y() < 0:
            self.goToNext()
        else:
            self.goToPrevious()
        e.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Left:
            self.goToPrevious()
            e.accept()
        elif e.key() == Qt.Key_Right:
            self.goToNext()
            e.accept()
        else:
            super().keyPressEvent(e)

    def resizeEvent(self, e):
        self._scaledPixmaps.clear()
        super().resizeEvent(e)

    def changeEvent(self, e):
        if e.type() in (QEvent.EnabledChange, QEvent.StyleChange, QEvent.PaletteChange):
            self.update()
        super().changeEvent(e)
