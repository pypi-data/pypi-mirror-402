#======================================================================
# SectorErrorDialog.py
#======================================================================
import logging
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTableWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidgetItem, QAbstractScrollArea, QStyle
)
from PyQt6.QtGui import QKeyEvent
from d64py.Constants import SectorErrors
from SectorErrorTable import SectorErrorTable
from SectorErrorModel import SectorErrorModel

class SectorErrorDialog(QMainWindow):
    def __init__(self, parent, flags, errorMap):
        super().__init__()
        self.parent = parent
        self.errorMap = errorMap
        self.realErrorMap = dict()
        row = 0
        for key in errorMap:
            if errorMap[key] in [SectorErrors.NOT_REPORTED.code, SectorErrors.NO_ERROR.code]:
                continue
            self.realErrorMap[key] = errorMap[key]

        self.tblErrors = SectorErrorTable(self)
        self.model = SectorErrorModel(self.realErrorMap)
        self.tblErrors.setModel(self.model)
        self.tblErrors.verticalHeader().hide()
        self.sizeTable()
        index = self.tblErrors.model().createIndex(0, 0)
        self.tblErrors.setCurrentIndex(index)

        button = QPushButton("&Close")
        button.clicked.connect(self.hide)
        hLayout = QHBoxLayout()
        hLayout.addStretch(1)
        hLayout.addWidget(button)
        hLayout.addStretch(1)
        vLayout = QVBoxLayout()
        vLayout.addWidget(self.tblErrors)
        vLayout.addLayout(hLayout)
        centralWidget = QWidget()
        centralWidget.setLayout(vLayout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle("sector errors")
        self.centerWindow()

    def sizeTable(self):
        i = 0; totalWidth = 0; longestErr = 0
        metrics = self.fontMetrics()
        while (i < self.model.columnCount(-1)):
            if i == 0:
                ttss = metrics.boundingRect("TT/SS").width() + 8 # fudge factor
                self.tblErrors.setColumnWidth(i, ttss)
                totalWidth += ttss
            else:
                longestMessage = 0
                for key in self.realErrorMap:
                    errCode = self.realErrorMap[key]
                    for err in SectorErrors:
                        if errCode == err.code:
                            value = err.description
                            break
                    errLength = metrics.boundingRect(value).width()
                    if errLength > longestErr:
                        longestErr = errLength + 8 # fudge factor
                self.tblErrors.setColumnWidth(1, longestErr)
                totalWidth += longestErr
            i += 1
        totalWidth += self.tblErrors.verticalScrollBar().width()
        self.tblErrors.setMinimumWidth(totalWidth)
        self.tblErrors.setMaximumWidth(totalWidth)
        self.tblErrors.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tblErrors.resizeColumnsToContents()

        totalHeight = 0;
        i = 0; rowCount = 8 if len(self.realErrorMap) >= 8 else len(self.realErrorMap)
        for i in range(rowCount - 1):
            if not self.tblErrors.verticalHeader().isSectionHidden(i):
                totalHeight += self.tblErrors.verticalHeader().sectionSize(i)
        if not self.tblErrors.horizontalScrollBar().isHidden():
            totalHeight += self.tblErrors.horizontalScrollBar().height()
        if not self.tblErrors.horizontalHeader().isHidden():
            totalHeight += self.tblErrors.horizontalHeader().height()
        frameWidth = self.tblErrors.frameWidth() * 2;
        self.tblErrors.setMinimumHeight(totalHeight + frameWidth)
        self.tblErrors.setMaximumHeight(totalHeight + frameWidth)

    def centerWindow(self):
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def keyPressEvent(self, evt: QKeyEvent):
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()
