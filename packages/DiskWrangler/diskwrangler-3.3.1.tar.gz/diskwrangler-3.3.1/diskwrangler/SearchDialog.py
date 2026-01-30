#======================================================================
# SearchDialog.py
#======================================================================
import logging
from pathlib import Path
from PyQt6.QtCore import Qt, QEvent, QThread
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (QMainWindow, QGroupBox, QHBoxLayout, QVBoxLayout,
    QGridLayout, QSizePolicy, QLabel, QLineEdit, QCheckBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QStatusBar, QWidget)
from Searcher import Searcher
from d64py import D64Utility
from d64py.DirEntry import DirEntry
from d64py.DiskImage import DiskImage, TextLine
from d64py.Constants import GeosFileType

class SearchDialog(QMainWindow):
    """
    Dialog for searching across a collection of disk images.
    """
    def __init__(self, parent, flags):
        super().__init__(parent, flags)
        self.parent = parent
        self.setContentsMargins(12, 12, 12, 12)

        textLayout = QGridLayout()
        #left, top, right, bottom
        textLayout.setContentsMargins(12, 0, 12, 12)
        textLayout.setSpacing(12)

        lblSearchFor = QLabel("Search for:")
        #widget, row, column[, rowSpan, columnSpan]:
        textLayout.addWidget(lblSearchFor, 0, 0)
        self.txtSearchFor = QLineEdit()
        #textLayout.addWidget(self.txtSearchFor, 0, 1, 1, 2)
        textLayout.addWidget(self.txtSearchFor, 0, 1)
        self.cmbPerm = QComboBox(self)
        self.cmbPerm.addItem("Write Image")
        self.cmbPerm.addItem("Paint Image")
        self.cmbPerm.addItem("GEOFILE IM")
        self.cmbPerm.addItem("Publish Doc")
        self.cmbPerm.addItem("Text  Scrap") # note extra space
        self.cmbPerm.addItem("text album")
        self.cmbPerm.addItem("Photo Scrap")
        self.cmbPerm.addItem("photo album")
        self.cmbPerm.activated.connect(self.permSelected)
        textLayout.addWidget(self.cmbPerm, 0, 2)

        lblStartingDir = QLabel("Starting dir:")
        textLayout.addWidget(lblStartingDir, 1, 0)
        self.txtStartingDir = QLineEdit()
        self.txtStartingDir.setText(self.parent.props["searchDir"].data)
        textLayout.addWidget(self.txtStartingDir, 1, 1)
        btnDirSelect = QPushButton("Se&lect")
        btnDirSelect.clicked.connect(self.dirSelectClicked)
        textLayout.addWidget(btnDirSelect, 1, 2)

        titleStyle = """
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                margin-left: 3px;
                margin-right: 3px;
            }
             QGroupBox {
                border: 1px ridge grey;
                border-radius: 0px;
                padding-top: 10px;
                margin-top: 5px;
            }
        """

        searchInBox = QGroupBox("Search in:")
        if parent.getApp().style().name().lower() == "fusion":
            searchInBox.setStyleSheet(titleStyle)
        searchInLayout = QVBoxLayout()
        searchInLayout.setContentsMargins(12, 12, 12, 12)
        searchInLayout.setSpacing(12)
        self.chkFileName = QCheckBox("file name", self)
        searchInLayout.addWidget(self.chkFileName)
        self.chkPermName = QCheckBox("permanent name", self)
        searchInLayout.addWidget(self.chkPermName)
        self.chkInfo = QCheckBox("info block", self)
        searchInLayout.addWidget(self.chkInfo)
        self.chkContents = QCheckBox("file contents", self)
        searchInLayout.addWidget(self.chkContents)
        searchInBox.setLayout(searchInLayout)

        fileTypeBox = QGroupBox("Search file types:")
        if parent.getApp().style().name().lower() == "fusion":
            fileTypeBox.setStyleSheet(titleStyle)
        self.chkFileTypes = []
        fileTypeLayout = QGridLayout()
        fileTypeLayout.setContentsMargins(12, 12, 12, 12)
        fileTypeLayout.setSpacing(6)
        i = 0; column = 0
        for fileType in GeosFileType:
            #15 file type checkboxes in three columns:
            self.chkFileTypes.append(QCheckBox(fileType.description, self))
            row = i
            if i > 4:
                row -= 5
            if i > 9:
                row -= 5 #another five
            fileTypeLayout.addWidget(self.chkFileTypes[i], row, column)
            if i == 4 or i == 9:
                column += 1
            i += 1

        btnAll = QPushButton("&All")
        btnAll.clicked.connect(self.selectAllFileTypes)
        fileTypeLayout.addWidget(btnAll, row + 1, 1, Qt.AlignmentFlag.AlignLeft)
        btnNone = QPushButton("&None")
        btnNone.clicked.connect(self.selectNoFileTypes)
        fileTypeLayout.addWidget(btnNone, row + 1, 2, Qt.AlignmentFlag.AlignLeft)
        fileTypeBox.setLayout(fileTypeLayout)

        searchButtonLayout = QHBoxLayout()
        btnTips = QPushButton("&Tips")
        btnTips.clicked.connect(self.tipsClicked)
        searchButtonLayout.addWidget(btnTips)
        btnSearch = QPushButton("&Search")
        btnSearch.clicked.connect(self.searchClicked)
        searchButtonLayout.addWidget(btnSearch)

        mainLayout = QGridLayout()
        mainLayout.setContentsMargins(0, 12, 12, 12)
        mainLayout.setSpacing(12)
        #widget, row, column[, rowSpan, columnSpan, alignment]:
        mainLayout.addLayout(textLayout, 0, 0, 1, 2)
        mainLayout.addWidget(searchInBox, 1, 0)
        mainLayout.addWidget(fileTypeBox, 1, 1)

        #mainLayout.addWidget(btnSearch, 2, 1, 1, 1, Qt.AlignmentFlag.AlignRight)
        mainLayout.addLayout(searchButtonLayout, 2, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)
        self.centerWindow()

    def permSelected(self):
        self.txtSearchFor.setText(self.cmbPerm.currentText())
        self.chkPermName.setCheckState(Qt.CheckState.Checked)

    def selectAllFileTypes(self):
        """
        Select all file types.
        """
        for chk in self.chkFileTypes:
            chk.setCheckState(Qt.CheckState.Checked)

    def selectNoFileTypes(self):
        """
        Deselect all file types.
        """
        for chk in self.chkFileTypes:
            chk.setCheckState(Qt.CheckState.Unchecked)

    def centerWindow(self):
        """
        Center window on screen.
        """
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def dirSelectClicked(self):
        """
        Handler for click on dir select button.
        """
        dir = QFileDialog.getExistingDirectory(self, "Select Starting Directory for Search",
                                               self.parent.props["searchDir"].data)
        self.txtStartingDir.setText(dir)

    def tipsClicked(self):
        """
        Handler for click on tips button: show explanatory dialog.
        """
        message = "If you enter a \"Search for:\", you must indicate\n" \
                  "where to search: select one or more of the\n" \
                  "checkboxes in \"Search in:\".\n\n" \
                  "\"File contents\" searches within geoWrite documents,\n" \
                  "text scraps, and text albums.\n\n" \
                  "The dropdown to the right of the search field holds\n" \
                  "permanent name string values for common GEOS\n" \
                  "document types. Selecting one will automatically\n" \
                  "select \"permanent name\".\n\n" \
                  "If you select any file types, the search will be\n" \
                  "limited to those files.\n\n" \
                  "You can also search only for file types (without a\n" \
                  "\"Search for:\"), in which case every file of that\n" \
                  "type will be returned."
        QMessageBox.information(self, "Search Tips", message, QMessageBox.StandardButton.Ok)
        return

    def searchClicked(self):
        """
        Handler for click on search button: validate data entry and perform search.
        :return: A list of TextLine, suitable for display in PlaintextDialog.
        """
        if not self.txtStartingDir.text().strip():
            QMessageBox.critical(self, "Error", "No starting directory specified.")
            return

        if self.chkFileName.isChecked() \
        or self.chkPermName.isChecked() \
        or self.chkInfo.isChecked()     \
        or self.chkContents.isChecked():
            if not self.txtSearchFor.text().strip():
                message = ("\"Search In\" entered, but no \"Search For\".\n" \
                           "Specity what to search for.")
                QMessageBox.critical(self, "Error", message,
                                        QMessageBox.StandardButton.Ok)
                return

        if self.txtSearchFor.text().strip():
            if not self.chkFileName.isChecked()  \
            and not self.chkPermName.isChecked() \
            and not self.chkInfo.isChecked()     \
            and not self.chkContents.isChecked():
                message = ("\"Search For\" entered, but no \"Search In\".\n" \
                           "Specify where to search.")
                QMessageBox.critical(self, "Error", message,
                                     QMessageBox.StandardButton.Ok)
                return
        else: #txtSearchFor is blank
            if not self.isFiletypeChecked():
                message = ("No \"Search For\" entered and\n"
                           "no filetypes selected. This\n"
                           "search would return all files.")
                QMessageBox.critical(self, "Error", message,
                                     QMessageBox.StandardButton.Ok)
                return

        #Validation passed, break off a thread to do the search:
        logging.debug("proceeding with search")
        self.parent.props["searchDir"] = self.txtStartingDir.text().strip()
        self.parent.writeProps()
        self.searchThread = QThread(self)
        self.searcher = Searcher(self)
        self.searcher.moveToThread(self.searchThread)
        self.searchThread.started.connect(self.searcher.run)
        self.searcher.progress.connect(self.parent.searchProgress)
        self.searcher.finished.connect(self.parent.searchComplete)
        self.searchThread.start()

    def isFiletypeChecked(self) -> bool:
        """
        Determine whether at least one filetype checkbox is checked.
        :return: True if at least one filetype is checked, False otherwise.
        """
        i = 0; checked = False
        while i < len(self.chkFileTypes):
            if self.chkFileTypes[i].isChecked():
                checked = True
                break
            i += 1
        return checked

    def selectedFiletypes(self) -> list:
        """
        Return a list of codes [indices] representing selected filetypes.
        :return: List of int.
        """
        selectedFiletypes = []
        i = 0
        while i < len(self.chkFileTypes):
            if self.chkFileTypes[i].isChecked():
                selectedFiletypes.append(i)
            i += 1
        return selectedFiletypes

    def keyPressEvent(self, evt: QKeyEvent):
        """
        Hide window when Escape is pressed.
        :param  evt The key event.
        """
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()
