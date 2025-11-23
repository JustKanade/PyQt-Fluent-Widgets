# coding:utf-8
import sys
from pathlib import Path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtGui import QColor, QPalette, QFont
from qfluentwidgets import (TransitionStackedWidget, TransitionType, PushButton, 
                            RadioButton, BodyLabel, SubtitleLabel, TitleLabel,
                            CardWidget, ScrollArea, setTheme, Theme,
                            isDarkTheme, FluentIcon as FIF, themeColor)
from qframelesswindow import FramelessWindow, StandardTitleBar


class ColorWidget(QFrame):
    """ colored rectangle widget """
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")


class SamplePage1(QWidget):
    """ Sample Page 1 matching WinUI Gallery """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.gridWidget = QWidget()
        self.gridLayout = QGridLayout(self.gridWidget)
        
        # Content text
        self.loremText = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

        # Blue box (SourceElement)
        self.blueBox = ColorWidget(themeColor())
        self.blueBox.setMinimumSize(200, 306)  # Adjusted size
        self.blueBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Gray boxes - using correct colors
        darkGray = QColor("#404040") if isDarkTheme() else QColor("#A0A0A0")
        lightGray = QColor("#606060") if isDarkTheme() else QColor("#D0D0D0")
        
        self.grayBox1 = ColorWidget(darkGray)
        self.grayBox2 = ColorWidget(lightGray)
        self.grayBox3 = ColorWidget(lightGray)
        self.grayBox4 = ColorWidget(darkGray)
        
        for box in [self.grayBox1, self.grayBox2, self.grayBox3, self.grayBox4]:
            box.setMinimumHeight(150)
            box.setMaximumHeight(150)

        # Layout setup
        # Column 0: Blue box (rowspan 2)
        self.gridLayout.addWidget(self.blueBox, 0, 0, 2, 1)
        
        # Column 1, 2: Gray boxes
        self.gridLayout.addWidget(self.grayBox1, 0, 1)
        self.gridLayout.addWidget(self.grayBox2, 0, 2)
        self.gridLayout.addWidget(self.grayBox3, 1, 1)
        self.gridLayout.addWidget(self.grayBox4, 1, 2)
        
        self.gridLayout.setSpacing(6)  # Tighter spacing like Gallery
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)

        # Text block at bottom
        self.textLabel = BodyLabel(self.loremText)
        self.textLabel.setWordWrap(True)
        self.textLabel.setStyleSheet("color: rgba(255, 255, 255, 0.786);" if isDarkTheme() else "color: rgba(0, 0, 0, 0.786);")
        
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.addWidget(self.gridWidget)
        self.vBoxLayout.addWidget(self.textLabel)
        self.vBoxLayout.addStretch(1)


class SamplePage2(QWidget):
    """ Sample Page 2 matching WinUI Gallery """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(24)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        # Blue box (DestinationElement)
        self.blueBox = ColorWidget(themeColor())
        self.blueBox.setFixedSize(150, 200)
        self.hBoxLayout.addWidget(self.blueBox, 0, Qt.AlignTop)
        
        # Text content
        self.textContainer = QWidget()
        self.textLayout = QVBoxLayout(self.textContainer)
        self.textLayout.setContentsMargins(0, 0, 0, 0)
        self.textLayout.setSpacing(12)
        
        self.titleLabel = TitleLabel("Lorem ipsum dolor sit amet, consectetur adipiscing elit")
        self.titleLabel.setWordWrap(True)
        
        self.loremText = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        self.bodyLabel = BodyLabel(self.loremText)
        self.bodyLabel.setWordWrap(True)
        
        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.bodyLabel)
        self.textLayout.addStretch(1)
        
        self.hBoxLayout.addWidget(self.textContainer, 1)
        self.hBoxLayout.addStretch(0)


class PageTransitionDemo(FramelessWindow):
    """ page transition demo window """
    
    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))
        self.setWindowTitle('Page Transition Demo')
        
        # create main layout
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 32, 0, 0)  # top margin for title bar
        
        # create content area (Left side)
        self.contentContainer = QWidget(self)
        self.contentContainer.setStyleSheet("background: transparent;")
        self.contentLayout = QVBoxLayout(self.contentContainer)
        self.contentLayout.setContentsMargins(48, 24, 24, 48)
        
        # create stacked widget with transitions
        self.stackedWidget = TransitionStackedWidget(self)
        
        # add sample pages
        self.pages = [SamplePage1(), SamplePage2()]
        for page in self.pages:
            self.stackedWidget.addWidget(page)
        
        self.contentLayout.addWidget(self.stackedWidget)
        
        # create control panel (Right side)
        self.controlPanel = QWidget(self)
        self.controlPanel.setFixedWidth(296)  # match Gallery width
        self.controlPanel.setStyleSheet(
            "QWidget { background-color: rgba(39, 39, 39, 0.95); border-left: 1px solid rgba(255, 255, 255, 0.08); }" 
            if isDarkTheme() else 
            "QWidget { background-color: rgba(243, 243, 243, 0.95); border-left: 1px solid rgba(0, 0, 0, 0.08); }"
        )
        
        self.controlLayout = QVBoxLayout(self.controlPanel)
        self.controlLayout.setSpacing(8)
        self.controlLayout.setContentsMargins(20, 32, 20, 20)
        
        # add title
        self.titleLabel = SubtitleLabel('Transition modes', self)
        self.titleLabel.setStyleSheet("padding: 0 0 4px 0;")
        self.controlLayout.addWidget(self.titleLabel)
        
        # create radio buttons for transitions
        self.transitionButtons = []
        self.transitions = [
            ('Default', TransitionType.DEFAULT),
            ('Entrance', TransitionType.ENTRANCE),
            ('Drill In', TransitionType.DRILL_IN),  # Note space in "Drill In"
            ('Suppress', TransitionType.SUPPRESS),
            ('Slide from Right', TransitionType.SLIDE_FROM_RIGHT),
            ('Slide from Left', TransitionType.SLIDE_FROM_LEFT),
        ]
        
        for name, transition in self.transitions:
            button = RadioButton(name, self)
            button.transition = transition
            button.toggled.connect(self.onTransitionChanged)
            self.transitionButtons.append(button)
            self.controlLayout.addWidget(button)
        
        # set default selection
        self.transitionButtons[1].setChecked(True)  # Entrance
        self.currentTransition = TransitionType.ENTRANCE
        
        # add separator
        self.controlLayout.addSpacing(20)
        
        # add navigation label
        self.navLabel = SubtitleLabel('Navigate', self)
        self.controlLayout.addWidget(self.navLabel)
        
        # add navigation buttons
        self.forwardButton = PushButton('Navigate Forward', self)
        self.forwardButton.clicked.connect(self.navigateForward)
        self.controlLayout.addWidget(self.forwardButton)
        
        self.backwardButton = PushButton('Navigate Backward', self)
        self.backwardButton.clicked.connect(self.navigateBackward)
        self.controlLayout.addWidget(self.backwardButton)
        
        self.controlLayout.addStretch(1)
        
        # add widgets to main layout
        self.mainLayout.addWidget(self.contentContainer, 1)
        self.mainLayout.addWidget(self.controlPanel)
        
        # set window properties
        self.resize(1024, 680)  # match Gallery size
        self.setStyleSheet("PageTransitionDemo{background: rgb(32, 32, 32)}" 
                          if isDarkTheme() else 
                          "PageTransitionDemo{background: rgb(251, 251, 251)}")
        
        # center window
        desktop = QApplication.desktop()
        rect = desktop.availableGeometry()
        self.move(rect.center() - self.rect().center())
        
        # raise title bar
        self.titleBar.raise_()
    
    def onTransitionChanged(self):
        """ handle transition mode change """
        for button in self.transitionButtons:
            if button.isChecked():
                self.currentTransition = button.transition
                break
    
    def navigateForward(self):
        """ navigate to next page """
        currentIndex = self.stackedWidget.currentIndex()
        nextIndex = (currentIndex + 1) % len(self.pages)
        
        # use different duration for different transitions
        duration = 250
        if self.currentTransition == TransitionType.DRILL_IN:
            duration = 350
        
        self.stackedWidget.setCurrentIndex(nextIndex, self.currentTransition, duration)
    
    def navigateBackward(self):
        """ navigate to previous page """
        currentIndex = self.stackedWidget.currentIndex()
        prevIndex = (currentIndex - 1) % len(self.pages)
        
        # for backward navigation with slide, reverse the direction
        transition = self.currentTransition
        if transition == TransitionType.SLIDE_FROM_RIGHT:
            transition = TransitionType.SLIDE_FROM_LEFT
        elif transition == TransitionType.SLIDE_FROM_LEFT:
            transition = TransitionType.SLIDE_FROM_RIGHT
        
        duration = 250
        if transition == TransitionType.DRILL_IN:
            duration = 350
            
        self.stackedWidget.setCurrentIndex(prevIndex, transition, duration)


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # set theme
    setTheme(Theme.AUTO)
    
    # create and show window
    window = PageTransitionDemo()
    window.show()
    
    sys.exit(app.exec_())
