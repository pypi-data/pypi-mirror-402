#======================================================================
# GeoPaintDialog.py
#======================================================================
import logging
from PyQt6.QtCore import Qt, QMargins, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QAbstractScrollArea, QMessageBox, QWidget, QSizePolicy
)

class GeoPaintDialog(QDialog):
    """
    Dialog for displaying geoPaint images.
    :param pixmap: The pixmap from the geoPaint image (double size).
    :param title: The filename of the image.
    """
    def __init__(self, parent, flags, pixmap: QPixmap, title: str):
        super().__init__(parent, flags)
        style = self.style() #QStyle
        self.titleHeight = style.pixelMetric(style.PixelMetric.PM_TitleBarHeight)
        self.pixmap = pixmap
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins()) # no margins

        lblPreview = QLabel("")
        lblPreview.setPixmap(self.pixmap) # image is double size

        if self.pixmap.height() >= self.screen().availableSize().height():
            self.scrImage = QScrollArea()
            self.scrImage.setWidget(lblPreview)
            self.scrImage.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.scrImage.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scrImage.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            self.scrImage.sizeHint = lambda: QSize(self.pixmap.width() + style.pixelMetric(style.PixelMetric.PM_ScrollBarExtent), self.screen().availableSize().height() - (self.titleHeight * 2))
            self.scrImage.ensureVisible(0, 0)
            layout.addWidget(self.scrImage)
        else:
            layout.addWidget(lblPreview)

        self.setLayout(layout)
        self.setWindowTitle(title)

    def sizeHint(self):
        if self.pixmap.height() < self.screen().availableSize().height():
            width = self.pixmap.width()
            height = self.pixmap.height()
        else:
            width = self.pixmap.width() + self.scrImage.verticalScrollBar().width() 
            height = self.screen().availableSize().height() - (self.titleHeight * 2)
        return QSize(width, height)
