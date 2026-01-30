#======================================================================
# BamModel.py
#======================================================================
import logging
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from d64py.TrackSector import TrackSector
from d64py import Geometry
from d64py.Constants import ImageType

class BamModel(QtCore.QAbstractTableModel):
    """
    Model class for tabular BAM display.
    """
    def __init__(self, image):
        super(BamModel, self).__init__()
        self.image = image
        self.bam = image.bam

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            track = index.row() + 1
            sector = index.column()
            if Geometry.isValidTrackSector(TrackSector(track, sector), self.image.imageType):
                allocated = self.image.isSectorAllocated(TrackSector(track, sector))
                return "X" if allocated else "O"
            else:
                return " "
        else:
            return None

    def headerData(self, section, orientation, role: Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                sector = "%02d" % (section)
                if sector[0] == '0':
                    return f"\n{sector[1]}"
                else:
                    return f"{sector[0]}\n{sector[1]}"
            else:
                return "%2d" % (section + 1)
        else:
            return None

    def rowCount(self, index):
        return Geometry.getMaxTrack(self.image.imageType)

    def columnCount(self, index):
        # track 1 will always have the most sectors:
        return Geometry.getMaxSector(self.image.imageType, 1) + 1

    def flags(self, index: QtCore.QModelIndex):
        # not checkable!
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
