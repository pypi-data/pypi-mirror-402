#======================================================================
# HexModel.py
#======================================================================
import logging
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableView
from HexTable import DisplayType

class HexModel(QtCore.QAbstractTableModel):
    def __init__(self, sector, editable: bool, table: QTableView):
        super(HexModel, self).__init__()
        self.sector = sector
        self.editable = editable
        self.displayType = DisplayType.HEX
        self.shifted = False # separate C= character set, not case shift

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            # (address is in vertical header)
            #     0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
            # 00: bb bb bb bb bb bb bb bb xx c  c  c  c  c  c  c  c
            if index.column() < 8: # hex display
                try:
                    byte = self.sector[(index.row() * 8) + index.column()]
                except Exception as exc:
                    logging.error(exc)
                return "%02x" % byte
            elif index.column() == 8: # hex/PETSCII separator
                return " "
            else: # PETSCII bytes
                #  use Unicode mapping from Style's TrueType CBM font
                char = self.sector[(index.row() * 8) + (index.column() - 9)]
                try:
                    # mimic Java's Character.isISOControl()
                    if char <= 0x1f or (char >= 0x7f and char <= 0x9f):
                        return '.'
                    else:
                        return chr(char | 0xe100 if self.shifted else char | 0xe000)
                except Exception as exc:
                    logging.error(exc)

    def setSectorData(self, sector):
        self.sector = sector
        self.refreshData()

    def setHeaderData(self, section: int, orientation: Qt.Orientation, data, role=Qt.ItemDataRole.DisplayRole):
        return super().setHeaderData(section, orientation, data, role)

    def headerData(self, section, orientation, role: Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return "%02x:" % (section * 8)

    def rowCount(self, index):
        return 32

    def columnCount(self, index):
        return 17

    def flags(self, index: QtCore.QModelIndex):
        if index.column() == 8:
            return Qt.ItemFlag.NoItemFlags
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role):
        if not self.editable:
            return
        if role == Qt.ItemDataRole.EditRole:
            try :
                if index.column() < 8:  # hex display
                    self.sector[(index.row() * 8) + index.column()] = int(value, base=16)
                elif index.column() > 8: # char display
                    try :
                        # strip Unicode high bits (0xe000 or 0xe100):
                        self.sector[(index.row() * 8) + (index.column() - 9)] = ord(value) & 0xff
                    except Exception as exc:
                        logging.error(f"in setData: {exc}")
            except Exception as exc:
                logging.error(f"in setData, value: {value}: {exc}")
            self.refreshData()
            return True

    def refreshData(self):
        topLeft = self.createIndex(0, 0)
        bottomRight = self.createIndex(31, 16)
        self.dataChanged.emit(topLeft, bottomRight, [Qt.ItemDataRole.DisplayRole])

    def dataChangedHandler(self):
        logging.debug("data changed")
