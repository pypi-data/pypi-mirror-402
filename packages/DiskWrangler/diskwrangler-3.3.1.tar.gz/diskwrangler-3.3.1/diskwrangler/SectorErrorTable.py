#======================================================================
# SectorErrorTable.py
#======================================================================
import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableView, QAbstractItemView

class SectorErrorTable(QTableView):
    def __init__(self, parent):
        super().__init__()
        self.verticalHeader().hide()
        font = self.horizontalHeader().font()
        font.setBold(False)
        self.horizontalHeader().setFont(font)
        self.horizontalHeader().setHighlightSections(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
