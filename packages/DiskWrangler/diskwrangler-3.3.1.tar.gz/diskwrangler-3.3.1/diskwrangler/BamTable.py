#======================================================================
# BamTable.py
#======================================================================
import logging
import os
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableView, QAbstractItemView, QHeaderView
from PyQt6.QtGui import QFont, QFontDatabase
from BamModel import BamModel

class BamTable(QTableView):
    """
    Table view to display a disk image's Block Availability Map.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        fontPath = str(Path(__file__).parents[0]) + os.sep + "C64_Pro_Mono-STYLE.ttf"
        fontId = QFontDatabase.addApplicationFont(fontPath)
        if fontId == -1:
            raise Exception("Can't load Style's Commodore font!")
        families = QFontDatabase.applicationFontFamilies(fontId)
        self.setFont(QFont(families[0], 10))
        self.verticalHeader().setFont(QFont(families[0], 10))
        self.horizontalHeader().setFont(QFont(families[0], 10))
        font = self.horizontalHeader().font()
        font.setBold(False)
        self.horizontalHeader().setFont(font)
        font = self.verticalHeader().font()
        font.setBold(False)
        self.verticalHeader().setFont(font)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

