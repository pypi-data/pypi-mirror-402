#======================================================================
# HexTable.py
#======================================================================
import os
from pathlib import Path
from enum import Enum, auto
import logging
from PyQt6.QtCore import Qt, QModelIndex, QEvent, QItemSelection
from PyQt6.QtGui import QFont, QFontDatabase, QAction, QKeyEvent, QFocusEvent
from PyQt6.QtWidgets import (
    QTableView, QTableWidgetItem, QAbstractItemDelegate, QMessageBox
)

class DisplayType(Enum):
    HEX = auto()
    CHAR = auto()

class HexTable(QTableView):
    def __init__(self, parent, editable: bool):
        super().__init__()
        self.parent = parent
        self.editable = editable
        self.editing = False

        fontPath = str(Path(__file__).parents[0]) + os.sep + "C64_Pro_Mono-STYLE.ttf"
        fontId = QFontDatabase.addApplicationFont(fontPath)
        if fontId == -1:
            raise Exception("Can't load Style's Commodore font!")
        families = QFontDatabase.applicationFontFamilies(fontId)
        self.setFont(QFont(families[0], 10))
        self.verticalHeader().setFont(QFont(families[0], 10))
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hexChars = bytes(b"0123456789ABCDEFabcdef")

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if selected.first(): # "selected" is a list of selection ranges
            column = selected.first().indexes()[0].column()
            if column < 9:
                self.model().displayType = DisplayType.HEX
            else:
                self.model().displayType = DisplayType.CHAR

    def keyPressEvent(self, evt: QKeyEvent):
        index = self.currentIndex()
        match evt.key():
            case Qt.Key.Key_Escape:
                self.parent.hide()
            # (address is in vertical header)
            #     0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
            # 00: bb bb bb bb bb bb bb bb xx c  c  c  c  c  c  c  c
            case Qt.Key.Key_Tab | Qt.Key.Key_Backtab:
                match self.model().displayType:
                    case DisplayType.CHAR:
                        self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() - 9)))
                    case DisplayType.HEX:
                        self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() + 9)))
                return

            case Qt.Key.Key_F: # control-F shifts C= font
                if evt.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.parent.shiftFont()
                    return

            case Qt.Key.Key_Left:
                match self.model().displayType:
                    case DisplayType.CHAR:
                        if index.column() > 9:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() - 1)))
                        else:
                            if index.row() > 0:
                                self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() - 1, 16)))
                    case DisplayType.HEX:
                        if index.column() > 0:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() - 1)))
                        else:
                            if index.row() > 0:
                                self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() - 1, 7)))
                return

            case Qt.Key.Key_Right:
                match self.model().displayType:
                    case DisplayType.CHAR:
                        if index.column() < 16:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() + 1)))
                        else:
                            if index.row() < 31:
                                self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() + 1, 9)))
                    case DisplayType.HEX:
                        if index.column() < 7:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), index.column() + 1)))
                        else:
                            if index.row() < 31:
                                self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() + 1, 0)))
                return

            case Qt.Key.Key_Up:
                if index.row() > 0:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() - 1, index.column())))
                return

            case Qt.Key.Key_Down:
                if index.row() < 31:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() + 1, index.column())))
                return

            case Qt.Key.Key_PageUp:
                if index.row() > 7:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() - 8, index.column())))
                else:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(0, index.column())))
                return

            case Qt.Key.Key_PageDown:
                if index.row() < 24:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row() + 8, index.column())))
                else:
                    self.setCurrentIndex(QModelIndex(self.model().createIndex(31, index.column())))
                return

            case Qt.Key.Key_Home:
                match self.model().displayType:
                    case DisplayType.HEX:
                        if evt.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(0, 0)))
                        else:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), 0)))
                    case DisplayType.CHAR:
                        if evt.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(0, 9)))
                        else:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), 9)))
                return

            case Qt.Key.Key_End:
                match self.model().displayType:
                    case DisplayType.HEX:
                        if evt.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(31, 7)))
                        else:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), 7)))
                    case DisplayType.CHAR:
                        if evt.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(31, 16)))
                        else:
                            self.setCurrentIndex(QModelIndex(self.model().createIndex(index.row(), 16)))
                return

        if not self.editable:
            return

        #============================
        # fall through: editing keys
        #============================
        match self.model().displayType:
            case DisplayType.CHAR:
                try:
                    if evt.key() < 256:
                        if not self.editing:
                            self.editing = True
                            self.edit(index)
                            # Insert trigger key as data:
                            editor = self.indexWidget(self.currentIndex()) # QLineEdit
                            editor.setMaxLength(1)
                            editor.textEdited.connect(self.edited)
                            # works, but need editor to do the same:
                            value = ord(evt.text().swapcase()) | 0xe100 if self.model().shifted \
                                else ord(evt.text().swapcase()) | 0xe000
                            try:
                                editor.insert(chr(value))
                            except Exception as exc:
                                logging.error(exc)
                except Exception as exc:
                    logging.error(exc)
                    logging.debug(f"char edit key: {evt.key()}")

            case DisplayType.HEX:
                try :
                    if evt.key() < 256 and evt.key() in self.hexChars:
                        if not self.editing:
                            self.editing = True
                            self.edit(index)
                            # Insert trigger key as data:
                            editor = self.indexWidget(self.currentIndex())
                            editor.setMaxLength(2)
                            try:
                                editor.insert(chr(evt.key()).lower())
                            except Exception as exc:
                                logging.error(exc)
                except Exception as exc:
                    logging.error(exc)
                    logging.debug(f"hex edit key: {evt.key()}")

    def edited(self, text: str):
        if not self.model().displayType == DisplayType.CHAR:
            return
        currentIndex = self.currentIndex()
        row = currentIndex.row()
        column = currentIndex.column()
        if row == self.model().rowCount(-1) - 1 and column == self.model().columnCount() - 1:
            return
        if column < 16:
            self.setCurrentIndex(QModelIndex(self.model().createIndex(row, column + 1)))
        else:
            self.setCurrentIndex(QModelIndex(self.model().createIndex(row + 1, 9)))

    def closeEditor(self, editor, hint):
        if self.editing:
            self.editing = False
            super().closeEditor(editor, QAbstractItemDelegate.EndEditHint.SubmitModelCache)

    def focusNextPrevChild(self, doFocus): # Override
        return False # avoids two events every time Tab is pressed
