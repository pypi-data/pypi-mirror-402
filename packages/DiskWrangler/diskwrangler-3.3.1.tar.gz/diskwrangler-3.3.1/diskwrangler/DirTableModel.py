#======================================================================
# DirTableModel.py
#======================================================================
from enum import Enum
import logging
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from d64py import DirEntry
from d64py.Constants import GeosFileType

class ModelFields(Enum):
    FILE_NAME = (0, "Name")
    FILE_SIZE = (1, "Blks")
    FILE_TYPE = (2, "Type")
    GEOS_FILE_TYPE = (3, "GEOS Type")
    GEOS_FILE_STRUCTURE = (4, "GEOS Struct")
    DATE_STAMP = (5, "Date Stamp")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    def code(self):
        return self.code()

    def description(self):
        return self.description

    def getDescriptionByCode(code: int):
        for e in ModelFields:
            if e.code == code:
                return e.description
        return None

    def getDescriptions(self) -> list[str]:
        descriptions = []
        for e in ModelFields:
            descriptions.append(e.description)
        return descriptions

#======================================================================

class DirTableModel(QtCore.QAbstractTableModel):
    """
    Data model for displaying a disk image's directory.
    """
    def __init__(self, dirEntries):
        super(DirTableModel, self).__init__()
        self.dirEntries = dirEntries

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            dirEntry = self.dirEntries[index.row()]
            match index.column():
                case ModelFields.FILE_NAME.code:
                    if dirEntry.getGeosFileType() == GeosFileType.NOT_GEOS:
                        return dirEntry.getDisplayFileName()
                    return dirEntry.getAsciiFileName()
                case ModelFields.FILE_SIZE.code:
                    return dirEntry.getFileSize()
                case ModelFields.FILE_TYPE.code:
                    return dirEntry.getFileTypeDescription()
                case ModelFields.GEOS_FILE_TYPE.code:
                    return dirEntry.getGeosFileType().description
                case ModelFields.GEOS_FILE_STRUCTURE.code:
                    if dirEntry.getGeosFileType() == GeosFileType.NOT_GEOS:
                        description = " "
                    else:
                        description = dirEntry.getGeosFileStructure().name
                    return description
                case ModelFields.DATE_STAMP.code:
                    return dirEntry.getFormattedDateStamp()

    def headerData(self, section, orientation, role: Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            try:
                for i in range(len(ModelFields)):
                    if i == section:
                        return ModelFields.getDescriptionByCode(i)
            except Exception as exc:
                print(str(exc))
        return super().headerData(section, orientation, role)

    def rowCount(self, index):
        return len(self.dirEntries)

    def columnCount(self, index):
        return len(ModelFields)

    def dataChangedHandler(self):
        logging.debug("data changed")

    def setDirEntries(self, dirEntries: list[DirEntry]):
        self.dirEntries = dirEntries
        topLeft = self.createIndex(0,0)
        bottomRight = self.createIndex(len(dirEntries), len(ModelFields))
        self.dataChanged.emit(topLeft, bottomRight, [Qt.ItemDataRole.DisplayRole])

    def getLongestName(self, metrics):
        longestName = 0
        if self.dirEntries:
            for dirEntry in self.dirEntries:
                nameLength = metrics.boundingRect(dirEntry.getAsciiFileName()).width()
                if nameLength > longestName:
                    longestName = nameLength
            return longestName
        else:
            # max. 16 characters in C= filename
            return metrics.boundingRect("M" * 16).width()
