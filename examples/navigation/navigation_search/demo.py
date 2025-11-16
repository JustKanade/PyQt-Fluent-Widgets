# coding:utf-8
import sys
import os

# Add parent directory to path to import local source
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget, QLabel

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationDisplayMode,
                            setTheme, Theme, FluentIcon as FIF, isDarkTheme)


class Widget(QWidget):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))
        
        # Apply style based on theme
        self.setStyleSheet("""
            Widget {
                background-color: transparent;
            }
            QLabel {
                font-size: 32px;
                font-weight: bold;
            }
        """)


class NavigationSearchDemo(QWidget):
    """ Navigation search demo """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Navigation Search Demo')
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        
        # Create navigation interface with search enabled
        self.navigationInterface = NavigationInterface(
            self,
            showMenuButton=True,
            showReturnButton=True,
            searchEnabled=True,  # Enable search functionality
            searchBoxWidth=300,  # Custom search box width
            searchCenterAlign=True,  # Center align search box
            searchAnimationDuration=250,  # Animation duration
            # searchIcon=FIF.ZOOM  # Custom search icon (optional)
        )
        
        # You can also configure these dynamically:
        # self.navigationInterface.setSearchBoxWidth(320)
        # self.navigationInterface.setSearchCenterAlign(False)
        # self.navigationInterface.setSearchAnimationDuration(300)
        # self.navigationInterface.setSearchButtonIcon(FIF.FILTER)
        
        # Customize search button tooltip (optional)
        # self.navigationInterface.setSearchButtonToolTip('Quick search')
        
        # Create stacked widget for pages
        self.stackedWidget = QStackedWidget(self)
        
        # Create main layout
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackedWidget, 1)
        
        # Create pages
        self.homeInterface = Widget('Home Page', self)
        self.musicInterface = Widget('Music Library', self)
        self.videoInterface = Widget('Video Player', self)
        self.folderInterface = Widget('File Explorer', self)
        self.settingInterface = Widget('Settings', self)
        self.albumInterface = Widget('Album Collection', self)
        self.playlistInterface = Widget('Playlists', self)
        self.favoriteInterface = Widget('Favorites', self)
        self.downloadInterface = Widget('Downloads', self)
        self.historyInterface = Widget('History', self)
        
        # Initialize navigation
        self.initNavigation()
        
        # Set default size
        self.resize(900, 700)
        
    def initNavigation(self):
        """ Initialize navigation """
        # Add main navigation items
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.musicInterface, FIF.MUSIC, 'Music')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, 'Video') 
        self.addSubInterface(self.folderInterface, FIF.FOLDER, 'Folder')
        
        # Add separator
        self.navigationInterface.addSeparator()
        
        # Add more navigation items
        self.addSubInterface(self.albumInterface, FIF.PHOTO, 'Album')
        self.addSubInterface(self.playlistInterface, FIF.MUSIC_FOLDER, 'Playlist')
        self.addSubInterface(self.favoriteInterface, FIF.HEART, 'Favorite')
        
        # Add bottom items
        self.navigationInterface.addSeparator(position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, 'Download', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.historyInterface, FIF.HISTORY, 'History', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
        
        # Set default page
        self.stackedWidget.setCurrentWidget(self.homeInterface)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())
        
        # Connect display mode change signal
        self.navigationInterface.displayModeChanged.connect(self.onNavigationDisplayModeChanged)
        
    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        """ Add sub interface """
        self.stackedWidget.addWidget(interface)
        item = self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position
        )
        return item
        
    def switchTo(self, widget):
        """ Switch to widget """
        self.stackedWidget.setCurrentWidget(widget)
        
    def onNavigationDisplayModeChanged(self, mode: NavigationDisplayMode):
        """ Handle navigation display mode change """
        if mode == NavigationDisplayMode.MINIMAL:
            self.navigationInterface.hide()
        else:
            self.navigationInterface.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    
    # Create window
    window = NavigationSearchDemo()
    window.show()
    
    sys.exit(app.exec_())
