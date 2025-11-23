# coding:utf-8
from enum import Enum

from PyQt5.QtCore import (QAbstractAnimation, QEasingCurve, QParallelAnimationGroup,
                          QPoint, QPointF, QPropertyAnimation, QRect, pyqtSignal, QVariantAnimation)
from PyQt5.QtGui import QTransform, QPainter, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget, QLabel


class TransitionType(Enum):
    """ Page transition types """
    DEFAULT = "default"
    ENTRANCE = "entrance"
    DRILL_IN = "drill_in"
    SUPPRESS = "suppress"
    SLIDE_FROM_RIGHT = "slide_from_right"
    SLIDE_FROM_LEFT = "slide_from_left"


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
    """ Stacked widget with multiple transition types precisely matching WinUI 3 """

    # WinUI 3 exact animation durations from source (ms)
    DURATION_OUT = 150           # Exit/fade out duration
    DURATION_IN = 300            # Enter/slide in duration  
    DURATION_DRILL_SCALE = 783   # DrillIn scale animation duration
    DURATION_DRILL_OPACITY = 333 # DrillIn opacity animation duration
    DURATION_DRILL_EXIT = 100    # DrillIn exit duration
    
    # WinUI 3 exact animation offsets from source
    ENTRANCE_OFFSET_Y = 140      # Vertical offset for entrance (from source)
    SLIDE_OFFSET_EXIT = 150      # Horizontal slide exit offset
    SLIDE_OFFSET_ENTER = -200    # Horizontal slide enter offset
    PARALLAX_RATIO = 0.25        # Parallax effect ratio (unchanged)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentAnimation = None
        self._nextIndex = None
        self._widgetEffects = {}  # widget -> QGraphicsOpacityEffect
        self._isAnimating = False
        self._easingCurves = self._createEasingCurves()
        self._snapshotLabels = []  # temporary labels for scale animations
        
    def addWidget(self, widget: QWidget):
        """ add widget with opacity effect """
        super().addWidget(widget)
        
        # add opacity effect for each widget
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(1.0)
        widget.setGraphicsEffect(effect)
        self._widgetEffects[widget] = effect
    
    def removeWidget(self, widget: QWidget):
        """ remove widget and its effect """
        if widget in self._widgetEffects:
            widget.setGraphicsEffect(None)
            del self._widgetEffects[widget]
        super().removeWidget(widget)
    
    def setCurrentIndex(self, index: int, transition: TransitionType = TransitionType.ENTRANCE, duration: int = None):
        """ set current index with transition
        
        Parameters
        ----------
        index: int
            target widget index
            
        transition: TransitionType
            transition type
            
        duration: int
            animation duration in milliseconds (auto-selected if None)
        """
        if index < 0 or index >= self.count():
            return
            
        if index == self.currentIndex():
            return
        
        # stop current animation
        if self._isAnimating and self._currentAnimation:
            if self._currentAnimation.state() == QAbstractAnimation.Running:
                self._currentAnimation.stop()
            self._onAnimationFinished()
        
        # suppress transition
        if transition == TransitionType.SUPPRESS:
            super().setCurrentIndex(index)
            return
        
        # auto-select duration based on transition type (not used for most animations)
        # Each animation type has its own specific timing
        
        # prepare widgets
        currentWidget = self.currentWidget()
        nextWidget = self.widget(index)
        self._nextIndex = index
        self._isAnimating = True
        
        # Switch index immediately for responsive layout
        # This allows Qt's layout system to start working right away
        super().setCurrentIndex(index)
        
        # Ensure both widgets are visible during animation
        if currentWidget:
            currentWidget.show()
            currentWidget.raise_()
        nextWidget.show()
        nextWidget.raise_()
        
        # create animation based on transition type
        if transition in [TransitionType.DEFAULT, TransitionType.ENTRANCE]:
            self._createEntranceAnimation(currentWidget, nextWidget, duration)
        elif transition == TransitionType.DRILL_IN:
            self._createDrillInAnimation(currentWidget, nextWidget, duration)
        elif transition == TransitionType.SLIDE_FROM_RIGHT:
            self._createSlideAnimation(currentWidget, nextWidget, duration, fromRight=True)
        elif transition == TransitionType.SLIDE_FROM_LEFT:
            self._createSlideAnimation(currentWidget, nextWidget, duration, fromRight=False)
        
        # start animation
        if self._currentAnimation:
            self._currentAnimation.finished.connect(self._onAnimationFinished)
            self._currentAnimation.start()
            
    def setCurrentWidget(self, widget: QWidget, transition: TransitionType = TransitionType.ENTRANCE, duration: int = None):
        """ set current widget with transition """
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index, transition, duration)
    
    def isAnimating(self):
        """ check if animation is running """
        return self._isAnimating
    
    def _createEasingCurves(self):
        """ create custom easing curves matching WinUI 3 cubic-bezier """
        curves = {}
        
        # Fast Out, Slow In - cubic-bezier(0.1, 0.9, 0.2, 1.0)
        # Used for entrance and slide animations
        fastOutSlowIn = QEasingCurve(QEasingCurve.BezierSpline)
        fastOutSlowIn.addCubicBezierSegment(
            QPointF(0.1, 0.9),   # control point 1
            QPointF(0.2, 1.0),   # control point 2
            QPointF(1.0, 1.0)    # end point
        )
        curves['fastOutSlowIn'] = fastOutSlowIn
        
        # Standard easing - cubic-bezier(0.8, 0.0, 0.2, 1.0)
        # More aggressive deceleration
        standard = QEasingCurve(QEasingCurve.BezierSpline)
        standard.addCubicBezierSegment(
            QPointF(0.8, 0.0),
            QPointF(0.2, 1.0),
            QPointF(1.0, 1.0)
        )
        curves['standard'] = standard
        
        # Accelerate - cubic-bezier(0.9, 0.1, 1.0, 0.2)
        # For exit animations
        accelerate = QEasingCurve(QEasingCurve.BezierSpline)
        accelerate.addCubicBezierSegment(
            QPointF(0.9, 0.1),
            QPointF(1.0, 0.2),
            QPointF(1.0, 1.0)
        )
        curves['accelerate'] = accelerate
        
        # Exit curve - cubic-bezier(0.7, 0.0, 1.0, 0.5)
        # For slide and entrance exit animations
        exitCurve = QEasingCurve(QEasingCurve.BezierSpline)
        exitCurve.addCubicBezierSegment(
            QPointF(0.7, 0.0),
            QPointF(1.0, 0.5),
            QPointF(1.0, 1.0)
        )
        curves['exitCurve'] = exitCurve
        
        return curves
    
    def _createEntranceAnimation(self, currentWidget: QWidget, nextWidget: QWidget, duration: int):
        """ create entrance animation (slide up + fade in) matching WinUI 3 exactly """
        self._currentAnimation = QParallelAnimationGroup(self)
        
        # WinUI 3: translationOffset = 140, outDuration = 150, inDuration = 300
        # Total duration = 450ms (150 + 300)
        
        # prepare next widget - set initial state
        nextWidget.move(0, self.ENTRANCE_OFFSET_Y)  # Start 140px below
        nextEffect = self._widgetEffects.get(nextWidget)
        if nextEffect:
            nextEffect.setOpacity(0.0)  # Start fully transparent
        nextWidget.show()
        nextWidget.raise_()
        
        # Use WinUI 3 control points for spline: (0.1, 0.9), (0.2, 1.0)
        entranceEasing = self._easingCurves.get('fastOutSlowIn', QEasingCurve.OutCubic)
        
        # WinUI 3: Opacity changes discretely at 150ms (outDuration)
        # We simulate this with a very fast transition at that time
        if nextEffect:
            # Create opacity animation that jumps from 0 to 1 at 150ms
            fadeIn = QPropertyAnimation(nextEffect, b'opacity', self)
            fadeIn.setDuration(self.DURATION_OUT + 10)  # 160ms total
            fadeIn.setKeyValueAt(0.0, 0.0)      # Start at 0
            fadeIn.setKeyValueAt(0.93, 0.0)     # Stay at 0 until ~150ms
            fadeIn.setKeyValueAt(1.0, 1.0)      # Jump to 1
            self._currentAnimation.addAnimation(fadeIn)
        
        # next widget: slide up from 140px over 450ms total
        # But the actual movement happens after the 150ms delay
        slideUp = QPropertyAnimation(nextWidget, b'pos', self)
        slideUp.setDuration(self.DURATION_OUT + self.DURATION_IN)  # 450ms total
        slideUp.setKeyValueAt(0.0, QPoint(0, self.ENTRANCE_OFFSET_Y))
        slideUp.setKeyValueAt(0.333, QPoint(0, self.ENTRANCE_OFFSET_Y))  # Hold for 150ms
        slideUp.setKeyValueAt(1.0, QPoint(0, 0))
        slideUp.setEasingCurve(entranceEasing)
        self._currentAnimation.addAnimation(slideUp)
        
        # current widget: fade out using WinUI 3 exit curve
        if currentWidget:
            currentEffect = self._widgetEffects.get(currentWidget)
            if currentEffect:
                # WinUI 3 uses (0.7, 0.0), (1.0, 0.5) for exit
                exitEasing = self._easingCurves.get('exitCurve', QEasingCurve.InCubic)
                fadeOut = QPropertyAnimation(currentEffect, b'opacity', self)
                fadeOut.setDuration(self.DURATION_OUT)  # 150ms
                fadeOut.setStartValue(1.0)
                fadeOut.setEndValue(0.0)
                fadeOut.setEasingCurve(exitEasing)
                self._currentAnimation.addAnimation(fadeOut)
    
    def _createDrillInAnimation(self, currentWidget: QWidget, nextWidget: QWidget, duration: int):
        """ create drill in animation (cross fade + scale) using snapshots for perfect effect """
        self._currentAnimation = QParallelAnimationGroup(self)
        
        # WinUI 3 DrillIn exact parameters from source:
        # NavigatingTo: scaleFactor = 0.94 (94% -> 100%), 783ms scale, 333ms opacity
        # NavigatingAway: scaleFactor = 1.04 (100% -> 104%), 100ms for both
        
        SCALE_FACTOR_IN = 0.94   # Start at 94% scale
        SCALE_FACTOR_OUT = 1.04  # Exit at 104% scale
        
        # Keep actual widgets at normal position for responsive layout
        nextWidget.move(0, 0)
        nextWidget.resize(self.size())
        
        # Create opacity curve: (0.17, 0.17), (0.0, 1.0)
        opacityEasing = QEasingCurve(QEasingCurve.BezierSpline)
        opacityEasing.addCubicBezierSegment(
            QPointF(0.17, 0.17),
            QPointF(0.0, 1.0),
            QPointF(1.0, 1.0)
        )
        
        # Create scale curve: (0.1, 0.9), (0.2, 1.0)
        scaleEasing = self._easingCurves.get('fastOutSlowIn', QEasingCurve.OutCubic)
        
        rect = self.rect()
        
        # Create snapshot of next widget for scale-in animation
        nextPixmap = QPixmap(nextWidget.size())
        nextWidget.render(nextPixmap)
        nextSnapshot = QLabel(self)
        nextSnapshot.setPixmap(nextPixmap)
        nextSnapshot.resize(nextWidget.size())
        self._snapshotLabels.append(nextSnapshot)
        
        # Set initial scaled geometry for snapshot
        scaledWidth = int(rect.width() * SCALE_FACTOR_IN)
        scaledHeight = int(rect.height() * SCALE_FACTOR_IN)
        offsetX = (rect.width() - scaledWidth) // 2
        offsetY = (rect.height() - scaledHeight) // 2
        scaledRect = QRect(offsetX, offsetY, scaledWidth, scaledHeight)
        
        nextSnapshot.setGeometry(scaledRect)
        nextSnapshot.show()
        nextSnapshot.raise_()
        
        # Add opacity effect to snapshot
        nextSnapshotEffect = QGraphicsOpacityEffect(nextSnapshot)
        nextSnapshotEffect.setOpacity(0.0)
        nextSnapshot.setGraphicsEffect(nextSnapshotEffect)
        
        # Animate snapshot scale to normal
        scaleIn = QPropertyAnimation(nextSnapshot, b'geometry', self)
        scaleIn.setDuration(self.DURATION_DRILL_SCALE)  # 783ms
        scaleIn.setStartValue(scaledRect)
        scaleIn.setEndValue(rect)
        scaleIn.setEasingCurve(scaleEasing)
        self._currentAnimation.addAnimation(scaleIn)
        
        # Animate snapshot fade in
        fadeInSnapshot = QPropertyAnimation(nextSnapshotEffect, b'opacity', self)
        fadeInSnapshot.setDuration(self.DURATION_DRILL_OPACITY)  # 333ms
        fadeInSnapshot.setStartValue(0.0)
        fadeInSnapshot.setEndValue(1.0)
        fadeInSnapshot.setEasingCurve(opacityEasing)
        self._currentAnimation.addAnimation(fadeInSnapshot)
        
        # Hide actual next widget during animation (it's already in correct position)
        nextWidget.hide()
        
        # Current widget: create snapshot and scale to 104%
        if currentWidget:
            currentPixmap = QPixmap(currentWidget.size())
            currentWidget.render(currentPixmap)
            currentSnapshot = QLabel(self)
            currentSnapshot.setPixmap(currentPixmap)
            currentSnapshot.resize(currentWidget.size())
            currentSnapshot.move(0, 0)
            self._snapshotLabels.append(currentSnapshot)
            
            currentSnapshot.show()
            currentSnapshot.raise_()
            
            # Add opacity effect
            currentSnapshotEffect = QGraphicsOpacityEffect(currentSnapshot)
            currentSnapshotEffect.setOpacity(1.0)
            currentSnapshot.setGraphicsEffect(currentSnapshotEffect)
            
            # Calculate exit scale (104%)
            exitWidth = int(rect.width() * SCALE_FACTOR_OUT)
            exitHeight = int(rect.height() * SCALE_FACTOR_OUT)
            exitOffsetX = -((exitWidth - rect.width()) // 2)
            exitOffsetY = -((exitHeight - rect.height()) // 2)
            exitRect = QRect(exitOffsetX, exitOffsetY, exitWidth, exitHeight)
            
            # Scale out animation
            scaleOut = QPropertyAnimation(currentSnapshot, b'geometry', self)
            scaleOut.setDuration(self.DURATION_DRILL_EXIT)  # 100ms
            scaleOut.setStartValue(rect)
            scaleOut.setEndValue(exitRect)
            scaleOut.setEasingCurve(scaleEasing)
            self._currentAnimation.addAnimation(scaleOut)
            
            # Fade out animation
            fadeOut = QPropertyAnimation(currentSnapshotEffect, b'opacity', self)
            fadeOut.setDuration(self.DURATION_DRILL_EXIT)  # 100ms
            fadeOut.setStartValue(1.0)
            fadeOut.setEndValue(0.0)
            fadeOut.setEasingCurve(opacityEasing)
            self._currentAnimation.addAnimation(fadeOut)
            
            # Hide actual current widget
            currentWidget.hide()
    
    def _createSlideAnimation(self, currentWidget: QWidget, nextWidget: QWidget, duration: int, fromRight: bool):
        """ create horizontal slide animation matching WinUI 3 exactly """
        self._currentAnimation = QParallelAnimationGroup(self)
        
        # WinUI 3 slide parameters from source:
        # translationExitOffset = 150px
        # translationEntranceOffset = -200px  
        # outDuration = 150ms, inDuration = 300ms
        # Opacity changes discretely at 150ms
        
        reverseSign = -1 if fromRight else 1
        
        # prepare next widget
        nextWidget.show()
        nextWidget.raise_()
        
        # Use WinUI 3 control points for spline: (0.1, 0.9), (0.2, 1.0)
        slideEasing = self._easingCurves.get('fastOutSlowIn', QEasingCurve.OutCubic)
        
        # next widget: slide in from SLIDE_OFFSET_ENTER
        slideIn = QPropertyAnimation(nextWidget, b'pos', self)
        slideIn.setDuration(self.DURATION_OUT + self.DURATION_IN)  # 450ms total
        # Start from -200px (or +200px if from left)
        slideIn.setKeyValueAt(0.0, QPoint(self.SLIDE_OFFSET_ENTER * reverseSign, 0))
        # Hold position for 150ms
        slideIn.setKeyValueAt(0.333, QPoint(self.SLIDE_OFFSET_ENTER * reverseSign, 0))
        # Slide to final position over 300ms
        slideIn.setKeyValueAt(1.0, QPoint(0, 0))
        slideIn.setEasingCurve(slideEasing)
        self._currentAnimation.addAnimation(slideIn)
        
        # next widget: discrete opacity change at 150ms
        nextEffect = self._widgetEffects.get(nextWidget)
        if nextEffect:
            fadeIn = QPropertyAnimation(nextEffect, b'opacity', self)
            fadeIn.setDuration(self.DURATION_OUT + 10)  # 160ms
            fadeIn.setKeyValueAt(0.0, 0.0)      # Start invisible
            fadeIn.setKeyValueAt(0.93, 0.0)     # Stay invisible until ~150ms
            fadeIn.setKeyValueAt(1.0, 1.0)      # Jump to visible
            self._currentAnimation.addAnimation(fadeIn)
        
        # current widget: slide out to SLIDE_OFFSET_EXIT  
        if currentWidget:
            # Use exit curve: (0.7, 0.0), (1.0, 0.5)
            exitEasing = self._easingCurves.get('exitCurve', QEasingCurve.InCubic)
            
            slideOut = QPropertyAnimation(currentWidget, b'pos', self)
            slideOut.setDuration(self.DURATION_OUT)  # 150ms
            slideOut.setStartValue(QPoint(0, 0))
            # Exit to 150px (or -150px if sliding left)
            slideOut.setEndValue(QPoint(self.SLIDE_OFFSET_EXIT * reverseSign, 0))
            slideOut.setEasingCurve(exitEasing)
            self._currentAnimation.addAnimation(slideOut)
            
            # current widget: discrete opacity change
            currentEffect = self._widgetEffects.get(currentWidget)
            if currentEffect:
                fadeOut = QPropertyAnimation(currentEffect, b'opacity', self)
                fadeOut.setDuration(self.DURATION_OUT + 10)  # 160ms
                fadeOut.setKeyValueAt(0.0, 1.0)      # Start visible
                fadeOut.setKeyValueAt(0.93, 1.0)     # Stay visible until ~150ms
                fadeOut.setKeyValueAt(1.0, 0.0)      # Jump to invisible
                self._currentAnimation.addAnimation(fadeOut)
    
    def _onAnimationFinished(self):
        """ handle animation finished and cleanup """
        self._isAnimating = False
        
        # Clean up snapshot labels
        for label in self._snapshotLabels:
            label.deleteLater()
        self._snapshotLabels.clear()
        
        # reset all widgets to default state
        for widget, effect in self._widgetEffects.items():
            effect.setOpacity(1.0)
            widget.move(0, 0)
            # reset geometry if it was scaled
            if widget.parent():
                widget.resize(self.size())
        
        # ensure only current widget is visible (index already switched at start)
        currentIndex = self.currentIndex()
        for i in range(self.count()):
            widget = self.widget(i)
            if i == currentIndex:
                widget.show()
            else:
                widget.hide()
        
        self._nextIndex = None
        
        if self._currentAnimation:
            self._currentAnimation.deleteLater()
            self._currentAnimation = None
