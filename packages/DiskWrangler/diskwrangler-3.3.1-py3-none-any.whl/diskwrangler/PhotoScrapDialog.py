#======================================================================
# PhotoScrapDialog.py
#======================================================================
import logging
from PyQt6.QtCore import Qt, QMargins
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QWidget
)
from PyQt6.QtGui import QAction
from d64gfx.D64Gfx import PhotoScrap

class PhotoScrapDialog(QMainWindow):
    """
    Dialog for displaying photo albums. To display a single photo scrap,
    pass a single-element list whose scrap has the name "Photo Scrap".
    :param scraps: The list of PhotoScrap objects to display.
    :param albumName: The name of the photo album containing the scraps.
    """
    def __init__(self, parent, flags, scraps: list[PhotoScrap], albumName: str):
        super().__init__()
        self.parent = parent
        self.scraps = scraps
        self.albumName = albumName
        self.setContentsMargins(12, 12, 12, 12)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(QMargins()) # no margins
        mainLayout.setSpacing(12)

        self.lblPreview = QLabel("")
        mainLayout.addWidget(self.lblPreview)

        if len(self.scraps) > 1:
            self.btnPrev = QPushButton("&Prev")
            self.btnPrev.clicked.connect(self.prev)
            self.btnPrev.setEnabled(False)
            self.btnNext = QPushButton("&Next")
            self.btnNext.clicked.connect(self.next)
            buttonLayout = QHBoxLayout()
            buttonLayout.addStretch(1)
            buttonLayout.addWidget(self.btnPrev)
            buttonLayout.addWidget(self.btnNext)
            mainLayout.addLayout(buttonLayout)

            menubar = self.menuBar()
            searchMenu = menubar.addMenu("&Search")
            self.searchActions = []
            i = 0
            while i < len(scraps):
                self.searchActions.append(QAction(scraps[i].name, self))
                self.searchActions[i].triggered.connect(self.showScrap)
                searchMenu.addAction(self.searchActions[i])
                i += 1
        
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

        self.currentScrap = 0; self.showScrap()

    def keyPressEvent(self, evt: QKeyEvent):
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()

    def showScrap(self):
        if len(self.scraps) > 1:
            action = self.sender()
            i = 0
            while i < len(self.searchActions):
                if action == self.searchActions[i]:
                    break
                i += 1
            if i < len(self.searchActions): # menu item selected?
                self.currentScrap = i
                if self.currentScrap == 0:
                    self.btnPrev.setEnabled(False)
                else:
                    self.btnPrev.setEnabled(True)
                if self.currentScrap == len(self.searchActions) - 1:
                    self.btnNext.setEnabled(False)
                else:
                    self.btnNext.setEnabled(True)
        
        scrap = self.scraps[self.currentScrap]
        self.lblPreview.setPixmap(scrap.bitmap)
        self.setWindowTitle(self.scraps[self.currentScrap].name)
        self.resize(scrap.bitmap.width(), scrap.bitmap.height())
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())
        
    def prev(self):
        self.currentScrap -= 1
        if self.currentScrap == 0:
            self.btnPrev.setEnabled(False)
        self.btnNext.setEnabled(True)
        self.showScrap()

    def next(self):
        self.currentScrap += 1
        if self.currentScrap == len(self.scraps) - 1:
            self.btnNext.setEnabled(False)
        self.btnPrev.setEnabled(True)
        self.showScrap()
