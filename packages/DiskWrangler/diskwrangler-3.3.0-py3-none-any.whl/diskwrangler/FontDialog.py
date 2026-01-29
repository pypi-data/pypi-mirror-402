#======================================================================
# FontDialog.py
#======================================================================
import logging
import traceback
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QGridLayout,
     QWidget, QMainWindow, QLabel, QLineEdit, QComboBox, QCheckBox,
     QPushButton, QMessageBox, QScrollArea, QSizePolicy)
from d64py import DiskImage, DirEntry
from d64py.TrackSector import TrackSector
from d64py.Constants import FontOffsets
from d64py import D64Utility
from d64gfx import D64Gfx

class FontDialog(QMainWindow):
    def __init__(self, parent, flags, dirEntry: DirEntry, diskImage: DiskImage):
        super().__init__(parent, flags)
        self.firstInit = True
        self.parent = parent
        self.dirEntry = dirEntry
        self.diskImage = diskImage
        self.fileHeader = self.diskImage.getGeosFileHeader(self.dirEntry)
        self.megaFont = self.diskImage.isMegaFont(dirEntry, self.fileHeader)

        self.setContentsMargins(12, 12, 12, 12)
        self.setWindowTitle("exploring font \"" + self.dirEntry.getDisplayFileName() + "\"")

        vbox = QVBoxLayout()
        vbox.setContentsMargins(12, 12, 12, 12)
        labelBox = QVBoxLayout()

        self.lblSample = QLabel("") # holds a Pixmap
        self.lblSample.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        scrImage = QScrollArea()
        scrImage.setWidgetResizable(True)
        scrImage.setWidget(self.lblSample)
        scrImage.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scrImage.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        labelBox.addWidget(scrImage)
        labelBox.addSpacing(12)
        vbox.addLayout(labelBox)
        vbox.addStretch(2)

        grid = QGridLayout()
        lblText = QLabel("text:")
        grid.addWidget(lblText, 0, 0)
        self.txtText = QLineEdit("Sphinx of black quartz, judge my vow.")

        metrics = self.txtText.fontMetrics()
        width = metrics.boundingRect('M' * 20).width()
        self.txtText.setMinimumWidth(width)
        self.txtText.setMaximumWidth(width)
        self.txtText.returnPressed.connect(self.showSample)
        grid.addWidget(self.txtText, 0, 1)

        lblPointSize = QLabel("point size:")
        grid.addWidget(lblPointSize, 1, 0)
        self.lblPointSizeData = QLabel("")
        if self.megaFont:
            self.megaFontData = self.diskImage.readMegaFontData(self.dirEntry)
            self.lblPointSizeData.setText(self.getMegaPointText())
            grid.addWidget(self.lblPointSizeData, 1, 1)
        else:
            cmbLayout = QHBoxLayout()
            self.cmbPointSize = QComboBox(self)
            pointSizes = self.fileHeader.getPointSizes()
            self.lblPointSizeData.setText(str(pointSizes[0]))
            for i in pointSizes:
                self.cmbPointSize.addItem(str(i))
            self.cmbPointSize.currentIndexChanged.connect(self.showSample)
            cmbLayout.addWidget(self.cmbPointSize)
            cmbLayout.addStretch(1)
            grid.addLayout(cmbLayout, 1, 1)

        lblStringWidth = QLabel("string width (pixels):")
        grid.addWidget(lblStringWidth, 3, 0)
        self.lblStringWidthData = QLabel("")
        grid.addWidget(self.lblStringWidthData, 3, 1)

        lblFontId = QLabel("font ID:")
        grid.addWidget(lblFontId, 4, 0)
        self.fontId = D64Utility.makeWord(self.fileHeader.getRaw(), FontOffsets.O_GHFONTID.value)
        lblFontIdData = QLabel("${:04X}".format(self.fontId) + f" ({self.fontId})")
        grid.addWidget(lblFontIdData, 4, 1)

        lblFontEscape = QLabel("font escape:")
        grid.addWidget(lblFontEscape, 5, 0)
        self.lblFontEscapeData = QLabel("")
        grid.addWidget(self.lblFontEscapeData, 5, 1)

        lblBaselineOffset = QLabel("baseline offset (pixels):")
        grid.addWidget(lblBaselineOffset, 6, 0)
        self.lblBaselineOffsetData = QLabel("")
        grid.addWidget(self.lblBaselineOffsetData, 6, 1)

        lblSetWidth = QLabel("set width (bytes):")
        grid.addWidget(lblSetWidth, 7, 0)
        self.lblSetWidthData = QLabel("")
        grid.addWidget(self.lblSetWidthData, 7, 1)

        vbox.addLayout(grid)

        buttonLayout = QHBoxLayout()
        btnClose = QPushButton("&Close")
        btnClose.clicked.connect(self.dismiss)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(btnClose)
        buttonLayout.addStretch(1)
        vbox.addLayout(buttonLayout)

        centralWidget = QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)
        self.showSample()
        self.centerWindow()

        self.txtText.setFocus()
        self.txtText.selectAll()
        
    def keyPressEvent(self, evt: QKeyEvent):
        match evt.key():
            case Qt.Key.Key_Escape:
                self.hide()

    def getMegaPointText(self):
        pointSize = 0

        for key in self.megaFontData.keys():
            if pointSize == 0:
                pointSize = self.megaFontData.get(key)[FontOffsets.F_HEIGHT.value]
            else:
                if not self.megaFontData.get(key)[FontOffsets.F_HEIGHT.value] == pointSize:
                    message = f"Multiple font heights in mega font headers,\nassuming {pointSize}."
                    QMessageBox.warning(None, "Warning", message, QMessageBox.StandardButton.Ok)
        return f"{pointSize} (mega font)"

    def centerWindow(self):
        rect = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def showSample(self):
        """
        Display a font sample for the current text in the current point size.
        """
        if self.megaFont:
            rawImage = D64Gfx.getMegaFontPreviewImage(self.txtText.text(),
                        self.megaFontData)
            fontImage = QPixmap.fromImage(rawImage)
            pixSize = fontImage.size()
            self.lblSample.setFixedSize(pixSize)
            self.lblSample.setPixmap(fontImage)
            stringWidth = D64Utility.getMegaStringWidth(self.txtText.text(), self.megaFontData)
            firstMegaRecord = self.megaFontData[list(self.megaFontData)[0]]
            pointSize = firstMegaRecord[FontOffsets.F_HEIGHT.value]
            baselineOffset = firstMegaRecord[FontOffsets.F_BASELN.value]
            setWidth = ""
            for key in self.megaFontData.keys():
                setWidth += "${:02X}".format(self.megaFontData[key][FontOffsets.F_SETWD.value])
                if not key == 54: # last record?
                    setWidth += "/"
        else:
            try:
                vlirIndex = self.diskImage.readSector(self.dirEntry.getFileTrackSector())
                pointSize = int(self.cmbPointSize.currentText())
                index = (pointSize + 1) * 2  # convert record no. to sector index
                ts = TrackSector(vlirIndex[index], vlirIndex[index + 1])
                fontData = self.diskImage.readChain(ts)
                baselineOffset = fontData[FontOffsets.F_BASELN.value]
                rawImage = D64Gfx.getFontPreviewImage(self.txtText.text(), fontData)
                fontImage = QPixmap.fromImage(rawImage)
                pixSize = fontImage.size()
                self.lblSample.setFixedSize(pixSize)
                self.lblSample.setPixmap(fontImage)
                setWidth = "${:04X}".format(fontData[FontOffsets.F_SETWD.value])
                stringWidth = D64Utility.getStringWidth(self.txtText.text(), fontData)
            except Exception as exc:
                logging.error(exc)
                traceback.print_exc()
            except BaseException as bxc:
                logging.error(bxc)
                traceback.print_exc()

        self.lblStringWidthData.setText(str(stringWidth))
        fontEscape = D64Utility.getFontEscape(self.fontId, pointSize)
        self.lblFontEscapeData.setText("${:04X}".format(fontEscape))
        self.lblBaselineOffsetData.setText(str(baselineOffset))
        self.lblSetWidthData.setText(setWidth) # pass formatted string

    def dismiss(self):
        self.hide()
