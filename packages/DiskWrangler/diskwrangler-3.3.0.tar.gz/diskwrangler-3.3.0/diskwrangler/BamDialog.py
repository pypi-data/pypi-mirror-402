#======================================================================
# BamDialog.py
#======================================================================
import logging
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QPushButton, QHeaderView, QWidget,
    QHBoxLayout
)
from BamTable import BamTable
from BamModel import BamModel

class BamDialog(QMainWindow):
    """
    Dialog for showing a disk image's Block Availability Map.
    """
    def __init__(self, parent, flags, diskImage):
        super().__init__()
        self.parent = parent
        self.diskImage = diskImage
        self.setContentsMargins(12, 12, 12, 12)
        try:
            self.tblBam = BamTable(self)
        except Exception as exc:
            raise exc
        self.model = BamModel(diskImage)
        self.tblBam.setModel(self.model)
        self.tblBam.resizeRowsToContents()
        self.tblBam.resizeColumnsToContents()
        index = self.tblBam.model().createIndex(0, 0)
        self.tblBam.setCurrentIndex(index)
        self.tblBam.setStyleSheet("""
            QHeaderView::section {
                background-color: #e0e0e0;
            }
            QTableView QTableCornerButton::section {
                background: #e0e0e0;
            }
        """)
        self.tblBam.clicked.connect(self.showTs)
        self.button = QPushButton("&Close")
        self.button.clicked.connect(self.dismiss)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.button)
        buttonLayout.addStretch(1)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.tblBam,2)
        self.lblBam = QLabel("")
        layout.addWidget(self.lblBam, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(buttonLayout, 1)
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(f"Block Availability Map for {diskImage.getDirHeader().getDiskName().strip()}")
        self.sizeTable()
        self.centerWindow()

    def showTs(self, item): # connected to tblBam clicked event
        track = self.model.headerData(item.row(), Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
        sector = self.model.headerData(item.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        # if item not selected, clear label
        if self.tblBam.selectionModel().isSelected(item):
            self.lblBam.setText(f"track {item.row() + 1}, sector {item.column()}: {"allocated" if item.data() == 'X' else "unallocated"}")
        else:
            self.lblBam.setText("")

    def sizeTable(self):
        horizontalHeader = self.tblBam.horizontalHeader()
        verticalHeader = self.tblBam.verticalHeader()
        width = 0; height = 0
        width += horizontalHeader.sectionSize(0) * self.model.columnCount(-1)
        width += verticalHeader.width()
        width += self.tblBam.verticalScrollBar().width()
        self.tblBam.setMinimumWidth(width)
        height = verticalHeader.sectionSize(0) * 35 # leave the same for D81
        height += horizontalHeader.height()
        self.tblBam.setMinimumHeight(height)

    def centerWindow(self):
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def keyPressEvent(self, evt: QKeyEvent):
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()

    def dismiss(self):
        self.hide()
