# coding:utf-8
from typing import Dict

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtSignal, QEasingCurve, QStringListModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFrame, QCompleter, QGraphicsOpacityEffect

from ...common.icon import FluentIconBase, FluentIcon as FIF
from ..widgets.line_edit import SearchLineEdit
from ..widgets.tool_tip import ToolTipFilter
from .navigation_widget import NavigationToolButton


class NavigationSearchBox(QFrame):
    """ Navigation search box with completer """

    searchSignal = pyqtSignal(str)
    itemClicked = pyqtSignal(str, str)  # routeKey, text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}  # type: Dict[str, str]
        self._itemTexts = []  # type: list
        self._textToKey = {}  # type: Dict[str, str]
        self.completer = None  # type: QCompleter

        self.searchEdit = SearchLineEdit(self)

        self._initWidget()
        self._initLayout()
        
    def _initWidget(self):
        """ initialize widget """
        self.setObjectName('navigationSearchBox')
        self.setFixedHeight(36)
        
        self.searchEdit.setPlaceholderText(self.tr('Search'))
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setFixedHeight(33)
        self.searchEdit.searchSignal.connect(self.searchSignal)

    def _initLayout(self):
        """ initialize layout """
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.searchEdit, 0, Qt.AlignVCenter)
        
    def addItem(self, routeKey: str, text: str, icon: FluentIconBase = None):
        """ add searchable item """
        self._items[routeKey] = text
        self._textToKey[text] = routeKey
        self._updateCompleter()

    def removeItem(self, routeKey: str):
        """ remove searchable item """
        if routeKey not in self._items:
            return
            
        text = self._items[routeKey]
        del self._items[routeKey]
        if text in self._textToKey:
            del self._textToKey[text]
        self._updateCompleter()

    def clearItems(self):
        """ clear all items """
        self._items.clear()
        self._textToKey.clear()
        self._updateCompleter()
        
    def setPlaceholderText(self, text: str):
        """ set search box placeholder text """
        self.searchEdit.setPlaceholderText(text)

    def _updateCompleter(self):
        """ update completer with current items """
        self._itemTexts = list(self._items.values())
        
        if not self._itemTexts:
            if self.completer:
                self.searchEdit.setCompleter(None)
                self.completer = None
            return

        if not self.completer:
            self.completer = QCompleter(self._itemTexts, self.searchEdit)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.setMaxVisibleItems(8)
            self.completer.activated[str].connect(self._onCompleterActivated)
            self.searchEdit.setCompleter(self.completer)
        else:
            model = QStringListModel(self._itemTexts)
            self.completer.setModel(model)

    def _onCompleterActivated(self, text: str):
        """ handle completer selection """
        if text not in self._textToKey:
            return
            
        routeKey = self._textToKey[text]
        self.itemClicked.emit(routeKey, text)
        self.searchEdit.clear()


class NavigationSearchWidget(QWidget):
    """ Navigation search widget """

    itemClicked = pyqtSignal(str, str)  # routeKey, text

    def __init__(self, parent=None, searchBoxWidth=280, centerAlign=True, animationDuration=250):
        """
        Parameters
        ----------
        parent: QWidget
            parent widget

        searchBoxWidth: int
            width of search box in expanded mode

        centerAlign: bool
            whether to center align the search box

        animationDuration: int
            animation duration in milliseconds
        """
        super().__init__(parent)
        self._isCompact = True
        self._searchBoxWidth = searchBoxWidth
        self._centerAlign = centerAlign
        self._animationDuration = animationDuration
        self._fromSearchButton = False

        self.searchButton = NavigationToolButton(FIF.SEARCH, self)
        self.searchBox = NavigationSearchBox(self)

        self.opacityEffect = QGraphicsOpacityEffect(self.searchBox)
        self.searchBox.setGraphicsEffect(self.opacityEffect)

        self.expandAni = QPropertyAnimation(self.searchBox, b'maximumWidth', self)
        self.expandAni.setDuration(animationDuration)
        self.expandAni.setEasingCurve(QEasingCurve.OutCubic)

        self.opacityAni = QPropertyAnimation(self.opacityEffect, b'opacity', self)
        self.opacityAni.setDuration(animationDuration)
        self.opacityAni.setEasingCurve(QEasingCurve.OutCubic)

        self._initWidget()
        self._initLayout()
        
    def _initWidget(self):
        """ initialize widget """
        self.setObjectName('navigationSearchWidget')
        self.setFixedHeight(36)

        self.searchButton.setToolTip(self.tr('Search'))
        self.searchButton.installEventFilter(ToolTipFilter(self.searchButton, 1000))

        self.searchBox.hide()
        self.searchBox.setMaximumWidth(0)

        self.searchButton.clicked.connect(self._onSearchButtonClicked)
        self.searchBox.itemClicked.connect(self.itemClicked)
        
    def _initLayout(self):
        """ initialize layout """
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        if self._centerAlign:
            self.hBoxLayout.addStretch(1)

        self.hBoxLayout.addWidget(self.searchButton, 0, Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.searchBox, 0, Qt.AlignVCenter)

        if self._centerAlign:
            self.hBoxLayout.addStretch(1)
        
    def setCompact(self, isCompact: bool):
        """ set compact mode """
        if self._isCompact == isCompact:
            return

        self._isCompact = isCompact

        if isCompact:
            self._collapseSearchBox()
        else:
            self._expandSearchBox()
            
    def _onSearchButtonClicked(self):
        """ handle search button click """
        self._fromSearchButton = True

        if self.parent():
            panel = self.parent()
            while panel and not hasattr(panel, 'expand'):
                panel = panel.parent()
            if panel and hasattr(panel, 'expand'):
                panel.expand()
                
    def _expandSearchBox(self):
        """ expand search box with animation """
        if self.expandAni.state() == QPropertyAnimation.Running:
            self.expandAni.stop()
            try:
                self.expandAni.finished.disconnect()
            except:
                pass

        if self.opacityAni.state() == QPropertyAnimation.Running:
            self.opacityAni.stop()
        
        self.searchButton.hide()
        self.searchBox.show()
        
        self.searchBox.setMinimumWidth(self._searchBoxWidth)

        self.expandAni.setStartValue(self.searchBox.width())
        self.expandAni.setEndValue(self._searchBoxWidth)
        self.expandAni.start()

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()

        if self._fromSearchButton:
            QTimer.singleShot(self._animationDuration, self.searchBox.searchEdit.setFocus)
            self._fromSearchButton = False
        
    def _collapseSearchBox(self):
        """ collapse search box with animation """
        self._fromSearchButton = False

        if self.expandAni.state() == QPropertyAnimation.Running:
            self.expandAni.stop()
            try:
                self.expandAni.finished.disconnect()
            except:
                pass

        if self.opacityAni.state() == QPropertyAnimation.Running:
            self.opacityAni.stop()

        self.searchBox.searchEdit.clear()
        self.searchBox.setMinimumWidth(0)

        self.searchButton.show()
        self.searchButton.raise_()

        self.opacityAni.setStartValue(1)
        self.opacityAni.setEndValue(0)
        self.opacityAni.start()

        self.expandAni.setStartValue(self.searchBox.width())
        self.expandAni.setEndValue(0)
        self.expandAni.finished.connect(self._onCollapseFinished)
        self.expandAni.start()
        
    def _onCollapseFinished(self):
        """ handle collapse animation finish """
        try:
            self.expandAni.finished.disconnect()
        except:
            pass
        self.searchBox.hide()
        self.opacityEffect.setOpacity(1)
        
    def addItem(self, routeKey: str, text: str, icon: FluentIconBase = None):
        """ add searchable item """
        self.searchBox.addItem(routeKey, text, icon)

    def removeItem(self, routeKey: str):
        """ remove searchable item """
        self.searchBox.removeItem(routeKey)

    def clearItems(self):
        """ clear all items """
        self.searchBox.clearItems()

    def setPlaceholderText(self, text: str):
        """ set search box placeholder text """
        self.searchBox.setPlaceholderText(text)

    def setSearchBoxWidth(self, width: int):
        """ set search box width in expanded mode """
        self._searchBoxWidth = width
        if not self._isCompact:
            self.searchBox.setMaximumWidth(width)
            self.searchBox.setMinimumWidth(width)

    def setCenterAlign(self, center: bool):
        """ set whether to center align the search box """
        if self._centerAlign == center:
            return

        self._centerAlign = center

        while self.hBoxLayout.count():
            item = self.hBoxLayout.takeAt(0)

        if self._centerAlign:
            self.hBoxLayout.addStretch(1)

        self.hBoxLayout.addWidget(self.searchButton, 0, Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.searchBox, 0, Qt.AlignVCenter)

        if self._centerAlign:
            self.hBoxLayout.addStretch(1)

    def setAnimationDuration(self, duration: int):
        """ set animation duration in milliseconds """
        self._animationDuration = duration
        self.expandAni.setDuration(duration)
        self.opacityAni.setDuration(duration)

    def setSearchButtonToolTip(self, text: str):
        """ set search button tooltip text """
        self.searchButton.setToolTip(text)
