# coding:utf-8
from enum import Enum
from typing import List

from PyQt5.QtCore import (QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation,
                          pyqtSignal, QParallelAnimationGroup)
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


class TransitionType(Enum):
    """ Transition type """
    DEFAULT = 0
    ENTRANCE = 1
    DRILL_IN = 2
    SUPPRESS = 3
    SLIDE_FROM_RIGHT = 4
    SLIDE_FROM_LEFT = 5


class OpacityAniStackedWidget(QStackedWidget):
    """ Stacked widget with fade in and fade out animation """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__nextIndex = 0
        self.__effects = []  # type:List[QPropertyAnimation]
        self.__anis = []     # type:List[QPropertyAnimation]

    def addWidget(self, w: QWidget):
        super().addWidget(w)

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        ani = QPropertyAnimation(effect, b'opacity', self)
        ani.setDuration(220)
        ani.finished.connect(self.__onAniFinished)
        self.__anis.append(ani)
        self.__effects.append(effect)
        w.setGraphicsEffect(effect)

    def setCurrentIndex(self, index: int):
        index_ = self.currentIndex()
        if index == index_:
            return

        if index > index_:
            ani = self.__anis[index]
            ani.setStartValue(0)
            ani.setEndValue(1)
            super().setCurrentIndex(index)
        else:
            ani = self.__anis[index_]
            ani.setStartValue(1)
            ani.setEndValue(0)

        self.widget(index_).show()
        self.__nextIndex = index
        ani.start()

    def setCurrentWidget(self, w: QWidget):
        self.setCurrentIndex(self.indexOf(w))

    def __onAniFinished(self):
        super().setCurrentIndex(self.__nextIndex)


class PopUpAniInfo:
    """ Pop up ani info """

    def __init__(self, widget: QWidget, deltaX: int, deltaY, ani: QPropertyAnimation):
        self.widget = widget
        self.deltaX = deltaX
        self.deltaY = deltaY
        self.ani = ani


class PopUpAniStackedWidget(QStackedWidget):
    """ Stacked widget with pop up animation """

    aniFinished = pyqtSignal()
    aniStart = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []  # type: List[PopUpAniInfo]
        self.isAnimationEnabled = True
        self._nextIndex = None
        self._ani = None

    def addWidget(self, widget, deltaX=0, deltaY=76):
        """ add widget to window

        Parameters
        -----------
        widget:
            widget to be added

        deltaX: int
            the x-axis offset from the beginning to the end of animation

        deltaY: int
            the y-axis offset from the beginning to the end of animation
        """
        super().addWidget(widget)

        self.aniInfos.append(PopUpAniInfo(
            widget=widget,
            deltaX=deltaX,
            deltaY=deltaY,
            ani=QPropertyAnimation(widget, b'pos'),
        ))

    def removeWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index == -1:
            return

        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setAnimationEnabled(self, isEnabled: bool):
        """set whether the pop animation is enabled"""
        self.isAnimationEnabled = isEnabled

    def setCurrentIndex(self, index: int, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                        duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """ set current window to display

        Parameters
        ----------
        index: int
            the index of widget to display

        isNeedPopOut: bool
            need pop up animation or not

        showNextWidgetDirectly: bool
            whether to show next widget directly when animation started

        duration: int
            animation duration

        easingCurve: QEasingCurve
            the interpolation mode of animation
        """
        if index < 0 or index >= self.count():
            return

        if index == self.currentIndex():
            return

        if not self.isAnimationEnabled:
            return super().setCurrentIndex(index)

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        # get the index of widget to be displayed
        self._nextIndex = index

        # get animation
        nextAniInfo = self.aniInfos[index]
        currentAniInfo = self.aniInfos[self.currentIndex()]

        currentWidget = self.currentWidget()
        nextWidget = nextAniInfo.widget
        ani = currentAniInfo.ani if needPopOut else nextAniInfo.ani
        self._ani = ani

        if needPopOut:
            deltaX, deltaY = currentAniInfo.deltaX, currentAniInfo.deltaY
            pos = currentWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, currentWidget.pos(), pos, duration, easingCurve)
            nextWidget.setVisible(showNextWidgetDirectly)
        else:
            deltaX, deltaY = nextAniInfo.deltaX, nextAniInfo.deltaY
            pos = nextWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, pos, QPoint(nextWidget.x(), 0), duration, easingCurve)
            super().setCurrentIndex(index)

        # start animation
        ani.finished.connect(self.__onAniFinished)
        ani.start()
        self.aniStart.emit()

    def setCurrentWidget(self, widget, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                         duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """ set currect widget

        Parameters
        ----------
        widget:
            the widget to be displayed

        isNeedPopOut: bool
            need pop up animation or not

        showNextWidgetDirectly: bool
            whether to show next widget directly when animation started

        duration: int
            animation duration

        easingCurve: QEasingCurve
            the interpolation mode of animation
        """
        self.setCurrentIndex(
            self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __setAnimation(self, ani, startValue, endValue, duration, easingCurve=QEasingCurve.Linear):
        """ set the config of animation """
        ani.setEasingCurve(easingCurve)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)

    def __onAniFinished(self):
        """ animation finished slot """
        self._ani.disconnect()
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()


class TransitionStackedWidget(QStackedWidget):
    """ Stacked widget with various transition animations """

    aniFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ani = None
        self._nextIndex = 0
        self.isAnimationEnabled = True

    def setCurrentIndex(self, index: int, transition=TransitionType.ENTRANCE, duration=250):
        """ set current widget with transition animation

        Parameters
        ----------
        index: int
            the index of widget to display

        transition: TransitionType
            transition type

        duration: int
            animation duration
        """
        if index < 0 or index >= self.count():
            return

        if index == self.currentIndex():
            return

        if not self.isAnimationEnabled or transition == TransitionType.SUPPRESS:
            super().setCurrentIndex(index)
            return

        # Clean previous animation
        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        self._nextIndex = index
        currentWidget = self.currentWidget()
        nextWidget = self.widget(index)
        
        if not currentWidget or not nextWidget:
            super().setCurrentIndex(index)
            return

        # Initialize effects
        self.__ensureEffect(currentWidget)
        self.__ensureEffect(nextWidget)

        # Create animation group
        self._ani = QParallelAnimationGroup(self)
        
        # Setup animation based on type
        if transition in [TransitionType.ENTRANCE, TransitionType.DEFAULT]:
            self.__setEntranceAnimation(currentWidget, nextWidget, duration)
        elif transition == TransitionType.DRILL_IN:
            self.__setDrillInAnimation(currentWidget, nextWidget, duration)
        elif transition == TransitionType.SLIDE_FROM_RIGHT:
            self.__setSlideAnimation(currentWidget, nextWidget, duration, fromRight=True)
        elif transition == TransitionType.SLIDE_FROM_LEFT:
            self.__setSlideAnimation(currentWidget, nextWidget, duration, fromRight=False)
        
        self._ani.finished.connect(self.__onAniFinished)
        self._ani.start()

    def setCurrentWidget(self, w: QWidget, transition=TransitionType.ENTRANCE, duration=250):
        """ set current widget with transition animation """
        self.setCurrentIndex(self.indexOf(w), transition, duration)

    def __ensureEffect(self, widget: QWidget):
        """ ensure widget has opacity effect """
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

    def __setEntranceAnimation(self, current: QWidget, next_: QWidget, duration: int):
        """ set entrance animation """
        # Ensure next widget is visible
        next_.resize(self.size())
        next_.show()
        next_.raise_()
        
        # Fix position in case it was moved by previous animation
        next_.move(0, 0)

        # Fade in
        next_.graphicsEffect().setOpacity(0)
        ani1 = QPropertyAnimation(next_.graphicsEffect(), b"opacity", self)
        ani1.setStartValue(0)
        ani1.setEndValue(1)
        ani1.setDuration(duration)
        ani1.setEasingCurve(QEasingCurve.OutQuad)
        
        # Slide up
        offset = 28
        pos = next_.pos()
        ani2 = QPropertyAnimation(next_, b"pos", self)
        ani2.setStartValue(pos + QPoint(0, offset))
        ani2.setEndValue(pos)
        ani2.setDuration(duration)
        ani2.setEasingCurve(QEasingCurve.OutCubic)
        
        self._ani.addAnimation(ani1)
        self._ani.addAnimation(ani2)

    def __setDrillInAnimation(self, current: QWidget, next_: QWidget, duration: int):
        """ set drill in animation """
        next_.resize(self.size())
        next_.show()
        next_.raise_()

        # Fade in
        next_.graphicsEffect().setOpacity(0)
        ani1 = QPropertyAnimation(next_.graphicsEffect(), b"opacity", self)
        ani1.setStartValue(0)
        ani1.setEndValue(1)
        ani1.setDuration(duration)
        ani1.setEasingCurve(QEasingCurve.OutQuad)
        
        # Fade out current
        ani2 = QPropertyAnimation(current.graphicsEffect(), b"opacity", self)
        ani2.setStartValue(1)
        ani2.setEndValue(0)
        ani2.setDuration(duration)
        ani2.setEasingCurve(QEasingCurve.OutQuad)

        self._ani.addAnimation(ani1)
        self._ani.addAnimation(ani2)

    def __setSlideAnimation(self, current: QWidget, next_: QWidget, duration: int, fromRight: bool):
        """ set slide animation """
        next_.resize(self.size())
        next_.show()
        next_.raise_()
        
        width = self.width()
        startX = width if fromRight else -width
        endX = -width // 2 if fromRight else width // 2
        
        # Next widget slide in
        ani1 = QPropertyAnimation(next_, b"pos", self)
        ani1.setStartValue(QPoint(startX, 0))
        ani1.setEndValue(QPoint(0, 0))
        ani1.setDuration(duration)
        ani1.setEasingCurve(QEasingCurve.OutQuint)
        
        # Current widget slide out (parallax)
        ani2 = QPropertyAnimation(current, b"pos", self)
        ani2.setStartValue(current.pos())
        ani2.setEndValue(QPoint(endX, 0))
        ani2.setDuration(duration)
        ani2.setEasingCurve(QEasingCurve.OutQuint)
        
        # Reset opacity
        current.graphicsEffect().setOpacity(1)
        next_.graphicsEffect().setOpacity(1)
        
        self._ani.addAnimation(ani1)
        self._ani.addAnimation(ani2)

    def __onAniFinished(self):
        """ animation finished slot """
        self._ani.disconnect()
        super().setCurrentIndex(self._nextIndex)
        self.widget(self._nextIndex).graphicsEffect().setOpacity(1)
        self.aniFinished.emit()
