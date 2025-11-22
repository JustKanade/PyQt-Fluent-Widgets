# coding:utf-8
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QApplication
from qfluentwidgets import (TransitionStackedWidget, TransitionType, RadioButton, 
                          PrimaryPushButton, PushButton, BodyLabel, SubtitleLabel,
                          TitleLabel, FluentWindow, setTheme, Theme, FluentIcon)


class Demo(FluentWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transition Stacked Widget Demo")
        self.resize(800, 650)

        # Main widget and layout
        self.mainWidget = QWidget(self)
        self.mainWidget.setObjectName("mainWidget")
        self.mainLayout = QHBoxLayout(self.mainWidget)
        self.addSubInterface(self.mainWidget, FluentIcon.HOME, "Home")

        # Control panel (Left side)
        self.controlPanel = QFrame(self.mainWidget)
        self.controlLayout = QVBoxLayout(self.controlPanel)
        self.controlPanel.setFixedWidth(300)
        
        self.titleLabel = TitleLabel("Page transitions", self.controlPanel)
        self.modeLabel = SubtitleLabel("Transition modes", self.controlPanel)
        
        self.defaultRb = RadioButton("Default", self.controlPanel)
        self.entranceRb = RadioButton("Entrance", self.controlPanel)
        self.drillInRb = RadioButton("DrillIn", self.controlPanel)
        self.suppressRb = RadioButton("Suppress", self.controlPanel)
        self.slideRightRb = RadioButton("Slide from Right", self.controlPanel)
        self.slideLeftRb = RadioButton("Slide from Left", self.controlPanel)
        
        self.defaultRb.setChecked(True)
        self.radioButtons = [
            self.defaultRb, self.entranceRb, self.drillInRb,
            self.suppressRb, self.slideRightRb, self.slideLeftRb
        ]
        
        self.navLabel = BodyLabel("Navigate", self.controlPanel)
        self.nextBtn = PrimaryPushButton("Navigate Forward", self.controlPanel)
        self.prevBtn = PushButton("Navigate Backward", self.controlPanel)

        self._initControlLayout()
        
        # Content area (Right side)
        self.stackedWidget = TransitionStackedWidget(self.mainWidget)
        
        # Add pages
        colors = ['#009faa', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff']
        for i, color in enumerate(colors):
            page = QFrame()
            page.setStyleSheet(f"QFrame{{background: {color}}}")
            label = TitleLabel(f"Page {i+1}", page)
            label.setStyleSheet("color: white")
            layout = QVBoxLayout(page)
            layout.addWidget(label, 0, Qt.AlignCenter)
            self.stackedWidget.addWidget(page)

        self.mainLayout.addWidget(self.controlPanel)
        self.mainLayout.addWidget(self.stackedWidget)
        
        # Connect signals
        self.nextBtn.clicked.connect(self.nextPage)
        self.prevBtn.clicked.connect(self.prevPage)
        
    def _initControlLayout(self):
        self.controlLayout.setSpacing(16)
        self.controlLayout.setContentsMargins(24, 24, 24, 24)
        self.controlLayout.addWidget(self.titleLabel)
        self.controlLayout.addSpacing(16)
        self.controlLayout.addWidget(self.modeLabel)
        
        for rb in self.radioButtons:
            self.controlLayout.addWidget(rb)
            
        self.controlLayout.addSpacing(16)
        self.controlLayout.addWidget(self.navLabel)
        self.controlLayout.addWidget(self.nextBtn)
        self.controlLayout.addWidget(self.prevBtn)
        self.controlLayout.addStretch(1)

    def getTransitionType(self):
        if self.entranceRb.isChecked():
            return TransitionType.ENTRANCE
        elif self.drillInRb.isChecked():
            return TransitionType.DRILL_IN
        elif self.suppressRb.isChecked():
            return TransitionType.SUPPRESS
        elif self.slideRightRb.isChecked():
            return TransitionType.SLIDE_FROM_RIGHT
        elif self.slideLeftRb.isChecked():
            return TransitionType.SLIDE_FROM_LEFT
        return TransitionType.DEFAULT

    def nextPage(self):
        count = self.stackedWidget.count()
        nextIndex = (self.stackedWidget.currentIndex() + 1) % count
        self.stackedWidget.setCurrentIndex(
            nextIndex, 
            transition=self.getTransitionType()
        )

    def prevPage(self):
        count = self.stackedWidget.count()
        prevIndex = (self.stackedWidget.currentIndex() - 1 + count) % count
        self.stackedWidget.setCurrentIndex(
            prevIndex, 
            transition=self.getTransitionType()
        )


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # setTheme(Theme.DARK)

    w = Demo()
    w.show()
    app.exec_()
