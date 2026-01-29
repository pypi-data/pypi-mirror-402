#======================================================================
# Searcher.py
#======================================================================
import logging
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox
import time
from d64py.DiskImage import DiskImage, TextLine, LineType
from d64py.DirEntry import DirEntry
from d64py.Constants import GeosFileType, FileType
from d64py.Exceptions import GeometryException,  PartialDirectoryException, PartialDataException

class Searcher(QObject):
    """
    This class searches for files based on user-selected parameters.
    It runs on its own thread and emits progress and finished signals.
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, searchDialog: QMainWindow):
        super().__init__()
        self.searchDialog = searchDialog

    def run(self):
        start = time.time()
        self.output = [] # list of TextLine
        self.hold = []   # hold lines to wait for elapsed time
        found = 0
        selectedFiletypes = self.searchDialog.selectedFiletypes()

        #input OK, proceed with search
        self.startingDir = Path(f"{self.searchDialog.txtStartingDir.text().strip()}")
        logging.debug(f"starting directory for recursive search: {self.searchDialog.txtStartingDir.text()}")
        if self.searchDialog.txtSearchFor.text().strip():
            self.hold.append(TextLine(f"Search for: {self.searchDialog.txtSearchFor.text().strip()}", LineType.HEADING))
        if self.searchDialog.chkFileName.isChecked() \
        or self.searchDialog.chkPermName.isChecked() \
        or self.searchDialog.chkInfo.isChecked()     \
        or self.searchDialog.chkContents.isChecked():
            message = "Search in: "
            first = True
            if self.searchDialog.chkFileName.isChecked():
                message += "filename"
                first = False
            if self.searchDialog.chkPermName.isChecked():
                if not first:
                    message += ", "
                message += "permanent name"
            if self.searchDialog.chkInfo.isChecked():
                if not first:
                    message += ", "
                message += "info block"
            if self.searchDialog.chkContents.isChecked():
                if not first:
                    message += ", "
                message += "file contents"
            self.hold.append(TextLine(message, LineType.HEADING))
            logging.debug(message)

        if selectedFiletypes:
            self.hold.append(TextLine("Search filetypes:", LineType.HEADING))
            for filetype in selectedFiletypes:
                for gft in GeosFileType:
                    if gft.code == filetype:
                        message = "  " + gft.description
                self.hold.append(TextLine(message, LineType.HEADING))
                logging.debug(message)

        self.hold.append(TextLine(f"Search from: {self.searchDialog.txtStartingDir.text()}", LineType.HEADING))

        imagesScanned = 0
        for root, directories, files in os.walk(self.startingDir):
            if ".git" in root or ".svn" in root:
                continue

            firstDiskHit = True
            for file in files:
                try:
                    diskImage = DiskImage(Path(root + os.sep + file))
                except Exception as exc:
                    continue # not a disk image

                message = f"checking image {file}"
                self.searchDialog.statusBar.showMessage(message)
                imagesScanned += 1

                try:
                    dirEntries = diskImage.getDirectory()
                except PartialDirectoryException as pxc:
                    logging.error(f"{diskImage.imagePath}: partial directory")
                    logging.error(pxc)
                    continue
                except GeometryException as gxc:
                    logging.error(f"{diskImage.imagePath}: bad geometry")
                    logging.error(gxc)
                    continue
                firstFileHit = True
                for dirEntry in dirEntries:
                    matchLines = self.fileMatches(dirEntry, diskImage)
                    if matchLines:
                        found += 1
                        if firstDiskHit:
                            self.output.append(TextLine("", LineType.NORMAL))
                            self.output.append(TextLine(f"directory {root}:", LineType.HEADING))
                            firstDiskHit = False
                        if firstFileHit:
                            self.output.append(TextLine("", LineType.NORMAL))
                            self.output.append(TextLine(os.path.basename(diskImage.imagePath), LineType.HEADING))
                            firstFileHit = False
                        self.output.extend(matchLines)
        self.searchDialog.statusBar.clearMessage()

        end = time.time()
        scanTime = "{:6.2f}".format(end - start).strip()
        message = f"Search complete. {imagesScanned} images scanned in {scanTime} seconds, {found} files found."
        self.progress.emit(message)
        self.hold.append(TextLine(message, LineType.HEADING))
        self.hold.extend(self.output)
        self.finished.emit(self.hold)

    def fileMatches(self, dirEntry: DirEntry, diskImage: DiskImage) -> list[TextLine]:
        """
        Determine if a file meets the search criteria.
        :param dirEntry The file to evaluate.
        :return: A list of TextLine to append to the search report.
        """
        match = False
        matchLines = []

        try:
            geosFileHeader = diskImage.getGeosFileHeader(dirEntry)
        except Exception as exc:
            geosFileHeader = None

        searchFor = self.searchDialog.txtSearchFor.text().strip()

        if not searchFor: # then do this section on its own
            if self.searchDialog.selectedFiletypes():
                for filetype in self.searchDialog.selectedFiletypes():
                    if filetype == dirEntry.getGeosFileType().code:
                        message = f"{dirEntry.getDisplayFileName()}: filetype matches ({dirEntry.getGeosFileType().description})"
                        matchLines.append(TextLine(message, LineType.NORMAL))
                return matchLines

        #--------------------------------------------------------------

        if self.searchDialog.chkFileName.isChecked():
            if searchFor.lower() in dirEntry.getDisplayFileName().lower():
                message = f"{dirEntry.getDisplayFileName()}: file name matches"
                matchLines.append(TextLine(message, LineType.NORMAL))
        if self.searchDialog.chkPermName.isChecked():
            if dirEntry.isGeosFile():
                try:
                    if geosFileHeader:
                        if searchFor.lower() in geosFileHeader.getPermanentNameString().lower():
                            message = f"{dirEntry.getDisplayFileName()}: permanent name matches: {dirEntry.getGeosFileHeader().getPermanentNameString()}"
                            matchLines.append(TextLine(message, LineType.NORMAL))
                except Exception as exc:
                    pass
        if self.searchDialog.chkInfo.isChecked():
            if geosFileHeader is not None:
                if searchFor.lower() in geosFileHeader.getInfo().lower():
                    message = f"{dirEntry.getDisplayFileName()}: info block matches:"
                    matchLines.append(TextLine(message, LineType.NORMAL))
                    message = geosFileHeader.getPlainInfo()
                    for line in message.split('\r'):
                      matchLines.append(TextLine("  " + line, LineType.NORMAL))

        #--------------------------------------------------------------

        if self.searchDialog.chkContents.isChecked():
            # is it a geoWrite file?
            if dirEntry.isGeosFile() and geosFileHeader is not None:
                if geosFileHeader.getParentApplicationName().startswith("geoWrite"):
                    try:
                        pages = diskImage.getGeoWriteFileAsLines(dirEntry)
                    except PartialDataException as pxc:
                        logging.debug(f"PartialDataException: {str(pxc)}")
                        pages = pxc.partialData
                    pageNumber = 1
                    for page in pages: # list of pages, which are lists of TextLine
                        firstTime = True
                        lineNumber = 1
                        for line in page:
                            # if caseSensitive:
                            #     hit = searchString in line.text
                            # else:
                            #     hit = searchString.lower() in line.text.lower()
                            hit = searchFor.lower() in line.text.lower()
                            if hit:
                                matchLines.append(TextLine(f"in geoWrite file '{dirEntry.getDisplayFileName()}':", LineType.HEADING))
                                matchLines.append(TextLine(f"page {pageNumber}, line {lineNumber}:", LineType.NORMAL))
                                # an entire paragraph can be one line:
                                if len(line.text) > 72:
                                    self.truncateText(line, searchFor.lower())
                                matchLines.append(line)
                            lineNumber += 1
                        pageNumber += 1

                # how about a text scrap?
                elif geosFileHeader.getPermanentNameString().startswith("Text  Scrap"):
                    firstTime = True
                    scrapLines = diskImage.getTextScrapAsText(dirEntry)
                    lineNumber = 1
                    for line in scrapLines:
                        # if caseSensitive:
                        #     hit = searchString in line.text
                        # else:
                        #     hit = searchString.lower() in line.text.lower()
                        hit = searchFor.lower() in line.text.lower()
                        if hit:
                            matchLines.append(TextLine(f"in Text Scrap:", LineType.HEADING))
                            matchLines.append(TextLine(f"line {lineNumber}:", LineType.NORMAL))
                            # in geoWrite, an entire paragraph can be one line:
                            if len(line.text) > 72:
                                self.truncateText(line, searchFor.lower())
                            matchLines.append(line)
                        lineNumber += 1

                # well then, what about a text album?
                elif geosFileHeader.getPermanentNameString().startswith("text album"):
                    matchLines = []
                    firstTime = True
                    try:
                        pages, scrapNames = self.searchDialog.parent.loadTextAlbum(dirEntry, diskImage)
                    except Exception as exc:
                        logging.debug(f"Can't read text album \"{dirEntry.getDisplayFileName()}\":")
                        logging.debug(str(exc))
                        QMessageBox.warning(None, "Error", str(exc), QMessageBox.StandardButton.Ok)
                    foundOne = False
                    lineNumber = 1
                    for index, page in enumerate(pages):
                        for line in page:
                            # if caseSensitive:
                            #     hit = searchString in line.text
                            # else:
                            #     hit = searchString.lower() in line.text.lower()
                            hit = searchFor.lower() in line.text.lower()
                            if hit:
                                if not foundOne:
                                    if firstTime:
                                        firstTime = False  # first time through, don't add a blank line
                                    else:
                                        matchLines.append(TextLine("", LineType.NORMAL))
                                    matchLines.append(TextLine(f"in text album \"{dirEntry.getDisplayFileName()}\":", LineType.HEADING))
                                    foundOne = True

                                matchLines.append(TextLine(f"scrap \"{scrapNames[index]}\", line {lineNumber}:", LineType.NORMAL))
                                # in geoWrite, an entire paragraph can be one line
                                if len(line.text) > 72:
                                    self.truncateText(line, searchFor.lower())
                                matchLines.append(line)
                            lineNumber += 1

        # if we didn't find anything, never mind the filetypes
        if matchLines:
            if self.searchDialog.selectedFiletypes():
                filetypeHit = False
                for filetype in self.searchDialog.selectedFiletypes():
                    if filetype == dirEntry.getGeosFileType().code:
                        filetypeHit = True
                        message = f"{dirEntry.getDisplayFileName()}: filetype matches ({dirEntry.getGeosFileType().description})"
                        matchLines.append(TextLine(message, LineType.NORMAL))
                if not filetypeHit:
                    matchLines.clear()

        return matchLines

    def truncateText(self, line: TextLine, searchFor: str):
        """
        Truncate long lines of search result text.
        :param line: The line of text to truncate.
        :param searchFor: The search target.
        """
        start = 0; end = 0
        pos = line.text.lower().index(searchFor.lower())
        end = len(line.text) - 1
        if pos > 0:
            i = pos
            while i > 0:
                i = i - 1
                if line.text[i] == ' ':
                    if pos - i > 34:
                        start = i
                        break
            if i == pos: # i.e. no hit
                start = 0

            i = pos
            while i < len(line.text):
                if line.text[i] == ' ':
                    if i - pos > 34:
                        end = i
                        break
                i = i + 1
            if i == pos: # i.e. no hit
                end = len(line.text)
            logging.debug(f"start: {start}, end: {end}")
            line.text = line.text[start:end]

    def codeFromDescription(self, description: str) -> int :
        """
        For the Geos filetype enum, get code from description.
        :param name: The display field's text.
        :return: The filetype's code.
        """
        code = -1
        for fileType in GeosFileType:
            if fileType.description == name:
                code = fileType.code
                break
        if code == -1:
            raise Exception(f"codeFromName(): {description} not found!")
        return code

    def nameFromCode(self, code: int) -> str:
        """
        For the Geos filetype enum, get description from code.
        :param code: The filetype's code.
        :return: The filetype's description.
        """
        description = ""
        for fileType in GeosFileType:
            if fileType.code == code:
                description = fileType.description
                break
        if description == "":
            raise Exception(f"nameFromCode(): {code} not found!")
        return description


