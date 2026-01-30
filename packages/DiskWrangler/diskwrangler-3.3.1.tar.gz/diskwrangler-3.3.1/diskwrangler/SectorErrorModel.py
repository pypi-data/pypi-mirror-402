#======================================================================
# SectorErrorModel.py
#======================================================================
import logging
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from d64py.Constants import SectorErrors

class SectorErrorModel(QtCore.QAbstractTableModel):
    def __init__(self, errorMap):
        super(SectorErrorModel, self).__init__()
        self.errorMap = errorMap

    def headerData(self, section, orientation, role: Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "T/S"
            else:
                return "error message"

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return str(list(self.errorMap)[index.row()]) # TrackSector
            else:
                errorCode = list(self.errorMap.values())[index.row()]
                errorMessage = SectorErrors.getSectorErrorDescription(errorCode)
                if errorMessage is None:
                    errorMessage = "unknown"
                return errorMessage

    def rowCount(self, index):
        return len(self.errorMap)

    def columnCount(self, index):
        return 2
