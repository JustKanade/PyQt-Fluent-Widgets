# coding:utf-8
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qfluentwidgets import (CaptionLabel, InfoBar, InfoBarPosition, StoreCarousel, StoreCarouselItem,
                            SwitchButton, Theme, setTheme)


class Demo(QWidget):

    def __init__(self):
        super().__init__()
        root = Path(__file__).resolve().parents[3]
        imageDir = root / 'source' / 'DevWinUI' / 'dev' / 'DevWinUI.Gallery' / 'Assets' / 'Carousel'
        images = [str(imageDir / f'{i}.jpg') for i in range(1, 11)]

        self.carousel = StoreCarousel(self)
        self.carousel.setFixedSize(735, 285)
        self.carousel.setItems([
            StoreCarouselItem(images[0], 'Alien', 'Survival horror in space', parameter='alien'),
            StoreCarouselItem(images[1], 'The Outer Worlds', 'A new colony awaits', parameter='outer-worlds'),
            StoreCarouselItem(images[2], 'Metro Exodus', 'Journey beyond the tunnels', parameter='metro'),
            StoreCarouselItem(images[3], 'Halo', 'Fight for humanity', parameter='halo'),
            StoreCarouselItem(images[4], 'Minecraft', 'Create and survive', parameter='minecraft'),
        ])
        self.carousel.setThumbnailImages(images[7], images[8], images[9])
        self.carousel.itemClicked.connect(self.onItemClicked)
        self.carousel.actionButtonClicked.connect(self.onActionClicked)

        self.carouselPanel = QWidget(self)
        self.carouselPanel.setFixedWidth(735)
        self.carouselLayout = QVBoxLayout(self.carouselPanel)
        self.carouselLayout.setContentsMargins(0, 26, 0, 0)
        self.carouselLayout.addWidget(self.carousel, 0, Qt.AlignTop)
        self.carouselLayout.addStretch()

        self.optionPane = QFrame(self)
        self.optionPane.setObjectName('optionPane')
        self.optionPane.setFixedWidth(283)

        self.autoShuffleLabel = CaptionLabel('Auto Shuffle', self.optionPane)
        self.autoShuffleSwitch = SwitchButton('\u5173', self.optionPane)
        self.autoShuffleSwitch.setChecked(True)
        self.autoShuffleSwitch.setOnText('\u5f00')
        self.autoShuffleSwitch.setOffText('\u5173')
        self.autoShuffleSwitch.setTextColor('#FFFFFF', '#FFFFFF')
        self.autoShuffleSwitch.setCheckedIndicatorColor('#4FEAFF', '#4FEAFF')
        self.autoShuffleSwitch.checkedChanged.connect(self.carousel.setAutoShuffle)

        self.optionLayout = QVBoxLayout(self.optionPane)
        self.optionLayout.setContentsMargins(16, 28, 0, 0)
        self.optionLayout.setSpacing(14)
        self.optionLayout.addWidget(self.autoShuffleLabel, 0, Qt.AlignLeft)
        self.optionLayout.addWidget(self.autoShuffleSwitch, 0, Qt.AlignLeft)
        self.optionLayout.addStretch()

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(18, 0, 0, 0)
        self.hBoxLayout.setSpacing(14)
        self.hBoxLayout.addWidget(self.carouselPanel)
        self.hBoxLayout.addWidget(self.optionPane)

        self.setObjectName('Demo')
        self.setStyleSheet("""
            Demo {
                background: #202428;
            }

            QFrame#optionPane {
                background: #202428;
                border-left: 1px solid #31363B;
            }
        """)
        self.resize(1050, 365)

    def onItemClicked(self, e):
        title = 'Thumbnail Clicked' if e.isThumbnail else 'Item Clicked'
        InfoBar.info(title, e.imageSource or e.title, duration=1500, position=InfoBarPosition.TOP, parent=self)

    def onActionClicked(self, e):
        InfoBar.success('Action Button Clicked', e.title, duration=1500, position=InfoBarPosition.TOP, parent=self)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    w = Demo()
    w.show()
    app.exec_()
