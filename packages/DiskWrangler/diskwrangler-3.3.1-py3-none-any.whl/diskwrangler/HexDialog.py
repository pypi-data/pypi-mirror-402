#======================================================================
# HexDialog.py
#======================================================================
import logging
from PyQt6.QtCore import Qt, QItemSelectionModel
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QMenu, QWidget, QHBoxLayout, QVBoxLayout,
    QAbstractItemView, QPushButton, QRadioButton, QLabel, QLineEdit, QStatusBar,
    QMessageBox
)
from d64py import Geometry
from d64py.TrackSector import TrackSector
from d64py.Exceptions import PartialChainException
from HexTable import HexTable, DisplayType
from HexModel import HexModel

class HexDialog(QMainWindow):
    def __init__(self, parent, flags, title: str, data, ts: TrackSector, editable: bool, showSelector: bool):
        super().__init__(parent, flags)
        self.parent = parent
        self.title = title
        self.data = data
        self.ts = ts
        self.editable = editable
        self.showSelector = showSelector

        self.setContentsMargins(12, 12, 12, 12)
        try:
            self.tblHex = HexTable(self, self.editable)
        except Exception as exc:
            raise exc
        self.hexModel = HexModel(data, self.editable, self.tblHex)
        self.tblHex.setStyleSheet("""
            QTableView QTableCornerButton::section {
                background: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
            }
        """)
        # turn off edit by double-click (we use that to initiate a sector jump):
        self.tblHex.setEditTriggers(QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.tblHex.setModel(self.hexModel)
        self.tblHex.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tblHex.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.tblHex.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tblHex.customContextMenuRequested.connect(self.showJumpContextMenu)
        
        self.tblHex.resizeRowsToContents()
        self.tblHex.resizeColumnsToContents()
        width = self.tblHex.horizontalHeader().length() + 48 # FIXME fudge factor
        height = self.tblHex.verticalHeader().length()  + 2  # FIXME fudge factor
        self.tblHex.setMinimumSize(width, height)
        index = self.hexModel.createIndex(0, 0)
        self.tblHex.setCurrentIndex(index)

        try:
            self.chain = self.parent.currentImage.followChain(ts)
        except PartialChainException as pce:
            self.chain = pce.partialChain
            msg = f"{pce}\n({self.chain.size()} sectors in chain)"
            QMessageBox.warning(None, "Warning", msg, QMessageBox.StandardButton.Ok)
        self.chainIndex = 0

        jumpAction = QAction("&Jump link", self)
        jumpAction.setShortcut("Ctrl+J")
        jumpAction.setStatusTip("jump to track/sector under cursor")
        jumpAction.triggered.connect(self.jumpLink)

        self.tblHex.doubleClicked.connect(self.jumpLink)

        self.nextAction = QAction("&Next in chain", self)
        self.nextAction.setShortcut("Ctrl+N")
        self.nextAction.setStatusTip("jump to next sector in chain")
        self.nextAction.triggered.connect(self.nextInChain)
        if self.chainIndex == self.chain.size() - 1:
            self.nextAction.setDisabled(True)

        self.prevAction = QAction("&Previous in chain", self)
        self.prevAction.setShortcut("Ctrl+P")
        self.prevAction.setStatusTip("jump to previous sector in chain")
        self.prevAction.triggered.connect(self.prevInChain)
        self.prevAction.setDisabled(True) # because we're starting at 0

        self.shiftAction = QAction("use shifted &font", self)
        self.shiftAction.setCheckable(True)
        self.shiftAction.setShortcut("Ctrl+F")
        self.shiftAction.setStatusTip("shift font")
        self.shiftAction.triggered.connect(self.shiftFont)

        menubar = self.menuBar()
        viewMenu = menubar.addMenu("&View")
        viewMenu.addAction(jumpAction)
        viewMenu.addAction(self.nextAction)
        viewMenu.addAction(self.prevAction)
        optionsMenu = menubar.addMenu("O&ptions")
        optionsMenu.addAction(self.shiftAction)

        hexLayout = QHBoxLayout()
        hexLayout.addWidget(self.tblHex, 1) # stretch factor

        if showSelector:
            radioLayout = QVBoxLayout()
            rdoHex = QRadioButton("&Hex", self)
            rdoHex.setChecked(True)
            radioLayout.addWidget(rdoHex)
            self.rdoAscii = QRadioButton("&Ascii", self)
            # with two radio buttons, one will do for both:
            self.rdoAscii.toggled.connect(self.setInputType)
            radioLayout.addWidget(self.rdoAscii)

            tsLayout = QHBoxLayout()
            tsLayout.addStretch(2)
            self.lblTrack = QLabel("&Track:  ")
            tsLayout.addWidget(self.lblTrack)
            self.txtTrack = QLineEdit(self)
            self.txtTrack.setMaxLength(2)
            maxWidth = self.txtTrack.fontMetrics().boundingRect("WW").width()
            self.txtTrack.setMaximumWidth(maxWidth)
            self.lblTrack.setBuddy(self.txtTrack)
            tsLayout.addWidget(self.txtTrack)
            tsLayout.addStretch(1)

            self.lblSector = QLabel("&Sector:  ")
            tsLayout.addWidget(self.lblSector)
            self.txtSector= QLineEdit(self)
            self.txtSector.setMaxLength(2)
            self.txtSector.setMaximumWidth(maxWidth)
            self.lblSector.setBuddy(self.txtSector)
            tsLayout.addWidget(self.txtSector)
            tsLayout.addStretch(1)
            tsLayout.addLayout(radioLayout)
            tsLayout.addStretch(2)

            buttonLayout = QHBoxLayout()
            buttonLayout.setSpacing(24)
            buttonLayout.addStretch(3)
            btnRead = QPushButton(text="&Read", parent=self)
            btnRead.clicked.connect(self.readSector)
            buttonLayout.addWidget(btnRead)
            buttonLayout.addSpacing(2)
            btnWrite = QPushButton(text="&Write", parent=self)
            btnWrite.clicked.connect(self.writeSector)
            buttonLayout.addWidget(btnWrite)
            buttonLayout.addStretch(3)

            self.statusBar = QStatusBar()
            self.statusBar.setSizeGripEnabled(False)
            self.statusBar.setContentsMargins(0, 0, 0, 0)
            # self.statusBar.setStyleSheet("border: 1px solid;")
            self.setStatusBar(self.statusBar)

            self.setInputType()

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(hexLayout)
        if showSelector:
            mainLayout.addLayout(tsLayout)
            mainLayout.addSpacing(12)
            mainLayout.addLayout(buttonLayout)
            mainLayout.addStretch(1)

        self.setTitle()
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)
        self.centerWindow()

    def setTitle(self):
        if self.rdoAscii.isChecked():
            tsString = str(self.ts)
            self.txtTrack.setText(f'{self.ts.track:02d}')
            self.txtSector.setText(f'{self.ts.sector:02d}')
        else:
            tsString = '$' + f'{self.ts.track:02x}' + '/' \
                     + '$' + f'{self.ts.sector:02x}'
            self.txtTrack.setText(f'{self.ts.track:02x}')
            self.txtSector.setText(f'{self.ts.sector:02x}')
        if self.title is None:
            self.setWindowTitle(self.parent.currentImage.imagePath.name + "  ("
            + self.parent.currentImage.imageType.description + ", sector "
            + tsString + ")")
        else:
            self.setWindowTitle(self.title + " (" + self.parent.currentImage.imageType.description + ", " + tsString + ")")

    def keyPressEvent(self, evt: QKeyEvent):
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()

    def centerWindow(self):
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def setInputType(self):
        if self.rdoAscii.isChecked():
            self.lblTrack.setText("&Track:  ")
            self.txtTrack.setInputMask("99") # just like COBOL!
            self.lblSector.setText("&Sector:  ")
            self.txtSector.setInputMask("99")
        else:
            self.lblTrack.setText("&Track: $")
            self.txtTrack.setInputMask("HH")
            self.lblSector.setText("&Sector: $")
            self.txtSector.setInputMask("HH")
        self.setTitle()

    def shiftFont(self):
        self.hexModel.shifted = not self.hexModel.shifted
        self.shiftAction.setChecked(self.hexModel.shifted)
        upperLeft = self.hexModel.createIndex(0, 0)
        lowerRight = self.hexModel.createIndex(31, 16)
        self.hexModel.dataChanged.emit(upperLeft, lowerRight)
        
    def showJumpContextMenu(self, pos):
        contextMenu = QMenu(self)
        jumpContextAction = QAction("View in New Window", self)
        jumpContextAction.triggered.connect(self.jumpNewWindow)
        contextMenu.addAction(jumpContextAction)
        contextMenu.exec(self.tblHex.mapToGlobal(pos))

    def jumpNewWindow(self):
        index = self.tblHex.selectedIndexes()[0] # table is set for single selection
        if self.hexModel.displayType == DisplayType.CHAR:
            offset = ((index.row() * 8) - 9) + index.column() # convert to hex offset
        else:
            offset = index.row() * 8 + index.column()
        if offset == 255:
            QMessageBox.warning(self, "Error", "Link must be two bytes.", QMessageBox.StandardButton.Ok)
            return
        ts = TrackSector(self.data[offset], self.data[offset + 1])
        if not Geometry.isValidTrackSector(ts, self.parent.currentImage.imageType):
            QMessageBox.warning(self, "Error", "Invalid track and sector.", QMessageBox.StandardButton.Ok)
            return
        sector = self.parent.currentImage.readSector(ts)
        try:
            # open in a new window:
            hexDialog = HexDialog(self.parent, Qt.WindowType.Dialog, None, sector, ts, True, True)
        except Exception as exc:
            QMessageBox.warning(self, "Warning", str(exc), QMessageBox.StandardButton.Ok)
            return
        hexDialog.show()

    def jumpLink(self):
        index = self.tblHex.selectedIndexes()[0] # table is set for single selection
        if self.hexModel.displayType == DisplayType.CHAR:
            offset = ((index.row() * 8) - 9) + index.column() # convert to hex offset
        else:
            offset = index.row() * 8 + index.column()
        if offset == 255:
            QMessageBox.warning(self, "Error", "Link must be two bytes.", QMessageBox.StandardButton.Ok)
            return
        ts = TrackSector(self.data[offset], self.data[offset + 1])
        if not Geometry.isValidTrackSector(ts, self.parent.currentImage.imageType):
            QMessageBox.warning(self, "Error", "Invalid track and sector.", QMessageBox.StandardButton.Ok)
            return
        self.ts = ts
        # User may have jumped outside of or into the middle of a chain,
        # but there's no easy way to detect that, so check for one:
        try:
            self.chain = self.parent.currentImage.followChain(self.ts)
        except PartialChainException as pce:
            self.chain = pce.partialChain
            msg = f"{pce}\n({self.chain.size()} sectors in chain)"
            QMessageBox.warning(None, "Warning", msg, QMessageBox.StandardButton.Ok)

        self.chainIndex = 0
        self.prevAction.setDisabled(True)
        if len(self.chain.sectors) == 1:
            self.nextAction.setDisabled(True)
        else:
            self.nextAction.setDisabled(False)
            
        self.data = self.parent.currentImage.readSector(self.chain.sectors[self.chainIndex])
        self.hexModel.setSectorData(self.data)
#        self.hexModel.layoutChanged.emit()
        self.setTsFields()
        index = self.hexModel.createIndex(0, 0)
        self.tblHex.selectionModel().setCurrentIndex(index, \
                    QItemSelectionModel.SelectionFlag.ClearAndSelect) # QModelIndex
        self.setTitle()

    def nextInChain(self):
        if (self.chainIndex == len(self.chain.sectors) - 1):
            return # no next in chain
        self.chainIndex += 1
        self.prevAction.setDisabled(False)
        if (self.chainIndex == len(self.chain.sectors) - 1):
            self.nextAction.setDisabled(True)
        self.ts = self.chain.sectors[self.chainIndex]
        self.data = self.parent.currentImage.readSector(self.chain.sectors[self.chainIndex])
        self.hexModel.setSectorData(self.data)
        self.setTsFields()
        index = self.hexModel.createIndex(0, 0)
        self.tblHex.selectionModel().setCurrentIndex(index, \
                    QItemSelectionModel.SelectionFlag.ClearAndSelect) # QModelIndex
        self.setTitle()

    def prevInChain(self):
        self.chainIndex -= 1
        self.nextAction.setDisabled(False)
        if self.chainIndex == 0:
            self.prevAction.setDisabled(True)
        self.ts = self.chain.sectors[self.chainIndex]
        self.data = self.parent.currentImage.readSector(self.chain.sectors[self.chainIndex])
        self.hexModel.setSectorData(self.data)
        self.setTsFields()
        index = self.hexModel.createIndex(0, 0)
        self.tblHex.selectionModel().setCurrentIndex(index, \
                    QItemSelectionModel.SelectionFlag.ClearAndSelect) # QModelIndex
        self.setTitle()

    def readSector(self):
        if not self.validateTrackSector(): # shows any error in a dialog
            return
        if self.rdoAscii.isChecked():
            self.ts = TrackSector(self.txtTrack.text(), self.txtSector.text())
        else:
            self.ts = TrackSector(int(self.txtTrack.text(), 16), int(self.txtSector.text(), 16))
        sector = self.parent.currentImage.readSector(self.ts)
        self.tblHex.model().setSectorData(sector)
        self.setTitle()
        self.tblHex.setFocus()

    def writeSector(self):
        if not self.validateTrackSector(): # shows any error in a dialog
            return
        if self.rdoAscii.isChecked():
            self.ts = TrackSector(self.txtTrack.text(), self.txtSector.text())
        else:
            self.ts = TrackSector(int(self.txtTrack.text(), 16), int(self.txtSector.text(), 16))
        self.parent.currentImage.writeSector(self.ts, self.hexModel.sector)
        if self.ts.track == Geometry.getDirectoryTrack(self.parent.currentImage.imageType):
            # if anything in the directory changed, reload the image:
            logging.info("directory changed, reloading image")
            self.parent.openImageFile(self.parent.currentImage.imagePath)
        else:
            self.setTitle()
        self.statusBar.showMessage(f"Sector {str(self.ts)} written.")
        self.tblHex.setFocus()

    def setTsFields(self):
        if self.rdoAscii.isChecked():
            self.txtTrack.setText(self.ts.track)

    def validateTrackSector(self):
        invalidTrack = False; invalidSector = False; messages = []
        if not self.txtTrack.text():
            messages.append("You must enter a track number.")
        if not self.txtSector.text():
            messages.append("You must enter a sector number.")

        if not messages:
            if self.rdoAscii.isChecked():
                track = int(self.txtTrack.text())
                sector = int(self.txtSector.text())
            else:
                try:
                    track = int(self.txtTrack.text(), 16)
                except Exception as exc:
                    messages.append("Invalid track number.")
                try:
                    sector = int(self.txtSector.text(), 16)
                except Exception as exc:
                    messages.append("Invalid sector number.")

        if not messages:
            ts = TrackSector(track, sector)
            if not Geometry.isValidTrackSector(ts, self.parent.currentImage.imageType):
                messages.append("Invalid track and sector for image type.")

        if messages:
            QMessageBox.warning(self, "Error", '\n'.join(messages), QMessageBox.StandardButton.Ok)
            return False

        return True
