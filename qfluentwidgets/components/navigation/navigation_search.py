# coding:utf-8
from typing import List, Dict
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtSignal, QEasingCurve, QStringListModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFrame, QCompleter

from ..widgets.line_edit import SearchLineEdit
from .navigation_widget import NavigationToolButton
from ...common.icon import FluentIconBase
from ...common.icon import FluentIcon as FIF




class NavigationSearchBox(QFrame):
    """ Navigation search box with completer """
    
    searchSignal = pyqtSignal(str)
    itemClicked = pyqtSignal(str, str)  # routeKey, text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}  # {routeKey: text}
        self._itemTexts = []  # List of texts for completer
        self._textToKey = {}  # {text: routeKey}
        
        # Create widgets
        self.searchEdit = SearchLineEdit(self)
        self.completer = None
        
        # Setup UI
        self._initWidget()
        self._initLayout()
        
    def _initWidget(self):
        """ Initialize widget """
        self.setObjectName('navigationSearchBox')
        self.searchEdit.setPlaceholderText(self.tr('Search'))
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setFixedHeight(32)
        
        # Connect signals
        self.searchEdit.searchSignal.connect(self.searchSignal)
        
    def _initLayout(self):
        """ Initialize layout """
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.searchEdit)
        
    def addItem(self, routeKey: str, text: str, icon: FluentIconBase = None):
        """ Add searchable item """
        self._items[routeKey] = text
        self._textToKey[text] = routeKey
        self._updateCompleter()
        
    def removeItem(self, routeKey: str):
        """ Remove searchable item """
        if routeKey in self._items:
            text = self._items[routeKey]
            del self._items[routeKey]
            if text in self._textToKey:
                del self._textToKey[text]
            self._updateCompleter()
            
    def clearItems(self):
        """ Clear all items """
        self._items.clear()
        self._textToKey.clear()
        self._updateCompleter()
        
    def _updateCompleter(self):
        """ Update completer with current items """
        self._itemTexts = list(self._items.values())
        
        if self._itemTexts:
            # Create completer
            if not self.completer:
                self.completer = QCompleter(self._itemTexts, self.searchEdit)
                self.completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.completer.setMaxVisibleItems(8)
                self.completer.activated[str].connect(self._onCompleterActivated)
                self.searchEdit.setCompleter(self.completer)
            else:
                # Update completer model
                model = QStringListModel(self._itemTexts)
                self.completer.setModel(model)
        elif self.completer:
            self.searchEdit.setCompleter(None)
            self.completer = None
            
    def _onCompleterActivated(self, text: str):
        """ Handle completer selection """
        if text in self._textToKey:
            routeKey = self._textToKey[text]
            self.itemClicked.emit(routeKey, text)
            self.searchEdit.clear()


class NavigationSearchWidget(QWidget):
    """ Navigation search widget that manages search button and search box """
    
    itemClicked = pyqtSignal(str, str)  # routeKey, text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._isCompact = True
        
        # Create widgets
        self.searchButton = NavigationToolButton(FIF.SEARCH, self)
        self.searchBox = NavigationSearchBox(self)
        
        # Animation
        self.expandAni = QPropertyAnimation(self.searchBox, b'maximumWidth', self)
        self.expandAni.setDuration(250)
        self.expandAni.setEasingCurve(QEasingCurve.OutCubic)
        
        self._initWidget()
        self._initLayout()
        
    def _initWidget(self):
        """ Initialize widget """
        self.setObjectName('navigationSearchWidget')
        self.searchButton.setToolTip(self.tr('Search'))
        
        # Initial state
        self.searchBox.hide()
        self.searchBox.setMaximumWidth(0)
        
        # Connect signals
        self.searchButton.clicked.connect(self._onSearchButtonClicked)
        self.searchBox.itemClicked.connect(self.itemClicked)
        
    def _initLayout(self):
        """ Initialize layout """
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.searchButton)
        self.hBoxLayout.addWidget(self.searchBox)
        
    def setCompact(self, isCompact: bool):
        """ Set compact mode """
        if self._isCompact == isCompact:
            return
            
        self._isCompact = isCompact
        
        if isCompact:
            # Show button, hide search box
            self._collapseSearchBox()
        else:
            # Hide button, show search box
            self._expandSearchBox()
            
    def _onSearchButtonClicked(self):
        """ Handle search button click """
        # Emit signal to expand navigation panel
        if self.parent():
            panel = self.parent()
            while panel and not hasattr(panel, 'expand'):
                panel = panel.parent()
            if panel and hasattr(panel, 'expand'):
                panel.expand()
                # Focus search box after expansion
                QTimer.singleShot(300, self.searchBox.searchEdit.setFocus)
                
    def _expandSearchBox(self):
        """ Expand search box with animation """
        self.searchButton.hide()
        self.searchBox.show()
        
        # Animate width
        self.expandAni.setStartValue(0)
        self.expandAni.setEndValue(280)
        self.expandAni.start()
        
        # Set focus after animation
        QTimer.singleShot(250, self.searchBox.searchEdit.setFocus)
        
    def _collapseSearchBox(self):
        """ Collapse search box with animation """
        # Clear search
        self.searchBox.searchEdit.clear()
        
        # Animate width
        self.expandAni.setStartValue(self.searchBox.width())
        self.expandAni.setEndValue(0)
        self.expandAni.finished.connect(self._onCollapseFinished)
        self.expandAni.start()
        
    def _onCollapseFinished(self):
        """ Handle collapse animation finish """
        self.expandAni.finished.disconnect()
        self.searchBox.hide()
        self.searchButton.show()
        
    def addItem(self, routeKey: str, text: str, icon: FluentIconBase = None):
        """ Add searchable item """
        self.searchBox.addItem(routeKey, text, icon)
        
    def removeItem(self, routeKey: str):
        """ Remove searchable item """
        self.searchBox.removeItem(routeKey)
        
    def clearItems(self):
        """ Clear all items """
        self.searchBox.clearItems()
