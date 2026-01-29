#======================================================================
# PlaintextDialog.py
#======================================================================
import logging
import os
from enum import Enum, auto
from pathlib import Path
from PyQt6 import QtGui, QtCore
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent, QScrollEvent, QPaintEvent
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import (QAction, QFont, QFontDatabase, QTextDocument,
                         QTextCursor, QResizeEvent)
from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QLineEdit,
    QComboBox, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QCheckBox,
    QPushButton, QMessageBox, QAbstractSlider)
from PyQt6.QtGui import QColor
from d64py.DirEntry import DirEntry
from d64py.Constants import CharSet
from d64py.Exceptions import PartialDataException
from d64py import D64Utility
from d64py.DiskImage import TextLine, LineType

class TextType(Enum):
    FILE     = auto()
    SCRAP    = auto()
    GEOWRITE = auto()
    SEARCH   = auto() #in geoWrite files
    ANALYSIS = auto()

class PlaintextHeight(Enum):
    TALL  = 35
    SHORT = 20

class PageChangeDirection(Enum):
    UP   = auto()
    DOWN = auto()

class PlaintextDialog(QMainWindow):
    """
    General-purpose dialog for displaying lines of text.
    :param textType: The type of text being displayed.
    :param pages: The text to display (list of lists of TextLine).
    :param charSet: Whether to display ASCII or PETSCII (enum).
    :param dirEntry: The DirEntry of the file to be displayed.
    """
    def __init__(self, parent, flags, textType: TextType, pages: list[list[TextLine]], charSet: CharSet, dirEntry: DirEntry=None):
        super().__init__(parent, flags)
        self.parent = parent

        self.textType = textType
        if (self.textType == TextType.SCRAP):
            self.plaintextHeight = PlaintextHeight.SHORT
        else:
            self.plaintextHeight = PlaintextHeight.TALL
        self.pages = pages
        self.charSet = charSet # PETSCII or ASCII
        self.dirEntry = dirEntry

        self.currentPage = 0
        self.paging = False
        self.pageLines = [] #last line number of each page
        self.pcd = PageChangeDirection(PageChangeDirection.DOWN)
        self.shifted = False
        self.settingPage = False

        self.setContentsMargins(12, 12, 12, 12)
        self.txtPlaintext = QTextEdit(self) # parent
        self.txtPlaintext.setMouseTracking(False)
        self.txtPlaintext.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
          | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.txtPlaintext.cursorPositionChanged.connect(self.cursorMoved)

        #viewport is a QWidget
        self.txtPlaintext.viewport().installEventFilter(self)
        viewport = self.txtPlaintext.viewport()

        self.plainFont = QFont("Monospace", 10)
        self.plainFont.setStyleHint(QFont.StyleHint.TypeWriter)

        fontPath = str(Path(__file__).parents[0]) + os.sep + "C64_Pro_Mono-STYLE.ttf"
        fontId = QFontDatabase.addApplicationFont(fontPath)
        if fontId == -1:
            raise Exception("Can't load Style's Commodore font!")
        families = QFontDatabase.applicationFontFamilies(fontId)
        self.commodoreFont = QFont(families[0], 10)

        if self.charSet == CharSet.PETSCII:
            self.txtPlaintext.setCurrentFont(self.commodoreFont)
        else:
            self.txtPlaintext.setCurrentFont(self.plainFont)

        shiftAction = QAction("use shifted &font", self)
        shiftAction.setShortcut("Ctrl+F")
        shiftAction.setStatusTip("shift font")
        shiftAction.triggered.connect(self.shiftFont)
        self.txtPlaintext.addAction(shiftAction)

        metrics = self.txtPlaintext.fontMetrics()
        width = metrics.boundingRect('n' * 78).width()
        height = (metrics.boundingRect('N').height() + 1) * self.plaintextHeight.value + 1
        self.txtPlaintext.setMinimumSize(width, height)
        self.plainColor = self.txtPlaintext.textColor()
        self.showTextLines()

        vLayout = QVBoxLayout()
        if self.textType != TextType.SCRAP:
            hLayout = QHBoxLayout()
            lblSearch = QLabel("&Search: ")
            self.txtSearch = QLineEdit()
            self.txtSearch.returnPressed.connect(self.doSearch)
            lblSearch.setBuddy(self.txtSearch)
            self.chkCaseSensitive = QCheckBox("&Case-sensitive", self)
            self.lblShift = QLabel("(ctrl-F shifts)")
            hLayout.addWidget(lblSearch)
            hLayout.addWidget(self.txtSearch)
            hLayout.addWidget(self.chkCaseSensitive)
            hLayout.addWidget(self.lblShift)
            # only put the button for C= text files
            if self.charSet == CharSet.PETSCII:
                self.btnCharSet = QPushButton("&ASCII", self)
                self.btnCharSet.clicked.connect(self.switchCharSet)
                hLayout.addWidget(self.btnCharSet)
                self.lblShift.setDisabled(False)
            else:
                self.lblShift.setDisabled(True)
            vLayout.addLayout(hLayout)

        vLayout.addWidget(self.txtPlaintext)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        self.btnPrev = QPushButton("&Prev")
        self.btnNext = QPushButton("&Next")
        self.cmbPage = None
        if self.textType == TextType.GEOWRITE:
            self.lblPage = QLabel("page:")
            buttonLayout.addWidget(self.lblPage)
            self.cmbPage = QComboBox()
            i = 0
            while i < len(self.pages):
                self.cmbPage.addItem(str(i + 1))
                i += 1
            buttonLayout.addWidget(self.cmbPage)

        if len(self.pages) > 1:
            if self.cmbPage:
                self.cmbPage.activated.connect(self.gotoPage)
                self.cmbPage.currentIndexChanged.connect(self.pageChanged)
            self.btnPrev.clicked.connect(self.prev)
            self.btnPrev.setEnabled(False)
            buttonLayout.addWidget(self.btnPrev)
            self.btnNext.clicked.connect(self.next)
            buttonLayout.addWidget(self.btnNext)
            vLayout.addLayout(buttonLayout)
        else:
            self.btnPrev.setEnabled(False)
            self.btnNext.setEnabled(False)
            if self.cmbPage:
                self.cmbPage.setEnabled(False)

        if self.textType == TextType.SCRAP:
            permString = self.dirEntry.geosFileHeader.getPermanentNameString()
            if permString.startswith("text album"): #i.e. album only, not scrap
                menubar = self.menuBar()
                self.searchMenu = menubar.addMenu("&Search")

        widget = QWidget()
        widget.setLayout(vLayout)
        self.setCentralWidget(widget)
        self.centerWindow()

    def cursorMoved(self):
        cursor = self.txtPlaintext.textCursor()

    def setScrapNames(self, scrapNames: list[str]):
        """
        Populate scrap search menu with names of scrap files in an album.
        :param  scrapNames The list of scraps in the album.
        """
        self.scrapNames = scrapNames
        self.searchActions = []
        i = 0
        while i < len(self.scrapNames):
            self.searchActions.append(QAction(self.scrapNames[i], self))
            self.searchActions[i].triggered.connect(self.searchScrap)
            self.searchMenu.addAction(self.searchActions[i])
            i += 1

    def keyPressEvent(self, evt: QKeyEvent):
        """
        Hide window when Escape is pressed.
        :param  evt The key event.
        """
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()

    def searchScrap(self):
        """
        Go to a specific scrap by clicking the scrap title in the menu.
        """
        if len(self.pages[self.currentPage]) > 1:
            action = self.sender()
            i = 0
            while i < len(self.searchActions):
                if action == self.searchActions[i]:
                    break
                i += 1
            if i < len(self.searchActions): # menu item selected?
                self.currentPage = i
                if self.currentPage == 0:
                    self.btnPrev.setEnabled(False)
                else:
                    self.btnPrev.setEnabled(True)
                if self.currentPage == len(self.searchActions) - 1:
                    self.btnNext.setEnabled(False)
                else:
                    self.btnNext.setEnabled(True)
        self.setWindowTitle(self.dirEntry.getDisplayFileName() + ": " + self.scrapNames[self.currentPage])
        self.showTextLines()

    def next(self):
        """
        Go to next page.
        """
        self.paging = True
        self.currentPage += 1
        self.gotoPage(self.currentPage)
        if self.textType == TextType.GEOWRITE:
            self.cmbPage.setCurrentIndex(self.currentPage)
            self.setWindowTitle(f"{self.dirEntry.getDisplayFileName()}, page {self.currentPage + 1}")
        self.paging = False

    def prev(self):
        """
        Go to previous page.
        """
        self.paging = True
        self.currentPage -= 1
        self.gotoPage(self.currentPage)
        if self.textType == TextType.GEOWRITE:
            self.setWindowTitle(f"{self.dirEntry.getDisplayFileName()}, page {self.currentPage + 1}")
        self.paging = False

    def reshow(self):
        """
        Repaint title bar and call showTextLines().
        """
        if self.dirEntry.geosFileHeader.getPermanentNameString().startswith("text album"):
            self.setWindowTitle(self.dirEntry.getDisplayFileName() + ": " + self.scrapNames[self.currentPage])
        else: #geoWrite
            self.setWindowTitle(f"{self.dirEntry.getDisplayFileName()}, page {self.currentPage + 1}")
        self.showTextLines()

    def pageChanged(self, page: int):
        """
        Set the paging direction for scroll adjustments: see gotoPage().
        This handler is connected to cmbPage.currentIndexChanged.
        It fires only when the page number combo box is changed.
        :param  page The page to switch to.
        """
        if self.currentPage != page:
            if page > self.currentPage:
                self.pcd = PageChangeDirection.DOWN
            else:
                self.pcd = PageChangeDirection.UP

    def gotoPage(self, index: int):
        """
        Go to a given page in the QTextEdit (connected to cmbPage.activated
        as well as the handlers for Next and Prev).
        :param  index The index of cmbPage.
        """
        if self.settingPage:
            return #avoid tunnel of mirrors
        self.btnPrev.setEnabled(True)
        self.btnNext.setEnabled(True)
        if index == 0:
            self.btnPrev.setEnabled(False)
        if index == len(self.pages) - 1:
            self.btnNext.setEnabled(False)

        if self.textType == TextType.GEOWRITE:
            cursor = self.txtPlaintext.textCursor()
            if index:
                pagePosition = self.pageLines[index]
            else:
                pagePosition = 0
            rect = self.txtPlaintext.cursorRect()
            viewportHeight = self.txtPlaintext.viewport().size().height()
            lineHeight = self.txtPlaintext.viewport().fontMetrics().height()
            viewportLines = (viewportHeight + lineHeight // 2) // lineHeight #round it
            cursor.setPosition(pagePosition, QTextCursor.MoveMode.MoveAnchor)
            self.txtPlaintext.setTextCursor(cursor)
            rect = self.txtPlaintext.cursorRect()

            #Paging down puts the top of the page at the bottom of the viewport.
            if rect.top() >= 4:
                linesToScroll = (rect.top() // lineHeight) + 5 #fudge factor
                if self.pcd == PageChangeDirection.DOWN:
                    cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, linesToScroll)
            self.txtPlaintext.setTextCursor(cursor)
            self.txtPlaintext.ensureCursorVisible()
            self.currentPage = index
            self.cmbPage.setCurrentIndex(self.currentPage)
        elif self.textType == TextType.SCRAP:
            self.reshow()

    def centerWindow(self):
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def showTextLines(self):
        """
        Show lines of text (self.pages) in the QTextEdit.
        """
        self.txtPlaintext.clear()
        cursor = self.txtPlaintext.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        lastIndex = len(self.pages) - 1

        try:
            if self.textType == TextType.SEARCH:
                self.txtPlaintext.setCurrentFont(self.plainFont)

            if self.textType == TextType.SCRAP:
                #for scraps, show one at a time and page through them with the buttons
                for line in self.pages[self.currentPage]:
                    self.showTextLine(line)
            else:
                self.pageLines.clear()   # first line number of each page
                self.pageLines.append(0) # first page
                for index, page in enumerate(self.pages, start=1):
                    firstLine = True
                    for line in self.pages[index - 1]:
                        self.showTextLine(line)
                        if firstLine:
                            position = self.txtPlaintext.textCursor().position()
                            firstLine = False
                    if self.textType == TextType.GEOWRITE:
                        if index -1 != lastIndex: #not after last page
                            self.txtPlaintext.setCurrentFont(self.plainFont)
                            self.txtPlaintext.insertHtml(f"<p><hr style=width: '95%'; height: '3px'; background-color: '#000';><br>")
                            self.txtPlaintext.setCurrentFont(self.plainFont)
                            position = self.txtPlaintext.textCursor().position()
                            self.pageLines.append(position)
        except Exception as exc:
            logging.exception(exc)
            return

        self.txtPlaintext.moveCursor(QTextCursor.MoveOperation.Start)
        vsb = self.txtPlaintext.verticalScrollBar() #QScrollBar
        vsb.valueChanged.connect(self.valueChanged)

    def showTextLine(self, line: TextLine):
        """
        Show a single text line.
        :param  line The TextLine to display.
        """
        match line.lineType:
            case LineType.NORMAL:
                self.txtPlaintext.append(line.text)
            case LineType.ERROR:
                self.txtPlaintext.setTextColor(QColor(255,48,0))
                self.txtPlaintext.append(line.text)
                self.txtPlaintext.setTextColor(self.plainColor)
            case LineType.HEADING:
                self.txtPlaintext.setFontWeight(QFont.Weight.Bold)
                self.txtPlaintext.append(line.text)
                self.txtPlaintext.setFontWeight(QFont.Weight.Normal)

    def valueChanged(self, evt: int):
        """
        Handler for change in value of scroll bar.
        :param  evt The ScrollEvent.
        """
        if self.paging:
            return #avoid tunnel of mirrors
        vsb = self.txtPlaintext.verticalScrollBar()
        scrollPct = evt / (vsb.maximum() or 1)
        try:
            scrollLine = self.pageLines[len(self.pageLines) - 1] * scrollPct
        except Exception as exc:
            return #probably not initialized yet
        i = 0
        thisPage = -1
        while i < len(self.pageLines):
            if scrollLine <= self.pageLines[i]:
                thisPage = i
                break
            i = i + 1
        self.settingPage = True
        self.currentPage = thisPage
        if self.textType == TextType.GEOWRITE:
            self.cmbPage.setCurrentIndex(thisPage)
            self.setWindowTitle(f"{self.dirEntry.getDisplayFileName()}, page {self.currentPage + 1}")
        if len(self.pages) > 1:
            if self.currentPage == 0:
                try:
                    self.btnPrev.setEnabled(False)
                    self.btnNext.setEnabled(True)
                except AttributeError as axc:
                    logging.debug(str(axc)) # should be fixed by double conditional above
            else:
                self.btnPrev.setEnabled(True)
                if self.currentPage == self.cmbPage.count() - 1:
                    self.btnNext.setEnabled(False)
                else:
                    self.btnNext.setEnabled(True)
        self.settingPage = False

    def eventFilter(self, obj, evt): #overridden
        if obj is self.txtPlaintext.viewport():
            if isinstance(evt, QPaintEvent):
                return super().eventFilter(obj, evt)

            elif isinstance(evt, QMouseEvent):
                position = self.txtPlaintext.cursorForPosition(evt.pos()).position()
                #position is character position in entire document
                i = 0
                thisPage = -1
                while i < len(self.pageLines):
                    try:
                        if position < self.pageLines[i]:
                            thisPage = i
                            break
                        i = i + 1
                    except Exception as exc:
                        logging.debug(exc)
                        logging.debug(f"position: {position}, i: {i}")
                        logging.debug(f"pageLines: ({len(self.pageLines)}): {self.pageLines}")

                if thisPage != -1 and self.textType == TextType.GEOWRITE:
                    try:
                        if thisPage != self.cmbPage.currentIndex():
                            self.settingPage = True
                            self.currentPage = thisPage
                            self.cbPage.setCurrentIndex(thisPage)
                            self.setWindowTitle(f"{self.dirEntry.getDisplayFileName()}, page {self.currentPage + 1}")
                            self.settingPage = False
                    except AttributeError as exc:
                        pass #probably not initialized yet

        return super().eventFilter(obj, evt)

    def shiftFont(self):
        """
        Shift Commodore font between upper-case and lower-case character sets, then redraw text.
        """
        if self.charSet == CharSet.ASCII:
            return
        self.shifted = not self.shifted
        self.pages = []
        self.txtPlaintext.setCurrentFont(self.commodoreFont)
        self.pages.append(self.parent.currentImage.getFileAsText(self.dirEntry, self.charSet, self.shifted))
        self.showTextLines()

    def switchCharSet(self):
        """
        Switch font between Monospace (ASCII) and Commodore (PETSCII).
        """
        self.txtPlaintext.clear()
        match self.charSet:
            case CharSet.ASCII: #switching to PETSCII
                self.txtPlaintext.setCurrentFont(self.commodoreFont)
                self.charSet = CharSet.PETSCII
                self.pages = []
                self.pages.append(self.parent.currentImage.getFileAsText(self.dirEntry, self.charSet, self.shifted))
                self.lblShift.setDisabled(False)
                self.btnCharSet.setText("&ASCII")
            case CharSet.PETSCII: #switching to ASCII
                self.txtPlaintext.setCurrentFont(self.plainFont)
                self.charSet = CharSet.ASCII
                self.pages = []
                self.pages.append(self.parent.currentImage.getFileAsText(self.dirEntry, self.charSet))
                self.lblShift.setDisabled(True)
                self.btnCharSet.setText("&PETSCII")
        self.showTextLines()

    def doSearch(self):
        """
        Search within geoWrite files on a disk image, or within an opened geoWrite file.
        """
        if not self.txtSearch.text():
            QMessageBox.warning(self, "Warning", "No search text entered.", QMessageBox.StandardButton.Ok)
            return

        if self.textType == TextType.SEARCH:
            # Call the Wrangler's searchWithinGeoWriteFiles()
            # to do the search and return a report.
            self.pages = self.parent.searchWithinGeoWriteFiles(
                         self.txtSearch.text(), self.chkCaseSensitive.isChecked())
            empty = True
            for page in self.pages:
                if page:
                    empty = False
                    break
            if not empty:
                self.txtSearch.setEnabled(False)
                self.showTextLines()
            else:
                QMessageBox.warning(self, "Warning", f"'{self.txtSearch.text()}' not found.", QMessageBox.StandardButton.Ok)
            return

        match self.charSet:
            case CharSet.ASCII:
                if self.chkCaseSensitive.isChecked():
                    result = self.txtPlaintext.find(self.txtSearch.text(), QTextDocument.FindFlag.FindCaseSensitively)
                else:
                    result = self.txtPlaintext.find(self.txtSearch.text())
            case CharSet.PETSCII:
                temp = D64Utility.asciiToPetsciiString(self.txtSearch.text())
                searchTerm = ""
                for char in temp:
                    searchTerm += chr(ord(char) | 0xe100 if self.shifted else ord(char) | 0xe000)
                result = self.txtPlaintext.find(D64Utility.asciiToPetsciiString(searchTerm))
        if not result:
            QMessageBox.warning(self, "Warning", f"'{self.txtSearch.text()}' not found!", QMessageBox.StandardButton.Ok)
