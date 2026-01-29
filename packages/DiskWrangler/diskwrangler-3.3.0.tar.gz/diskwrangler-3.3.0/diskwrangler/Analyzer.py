#======================================================================
# Analyzer.py
#======================================================================
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from d64py.Constants import GeosFileStructure
from d64py.DirEntry import DirEntry
from d64py.Chain import Chain
from d64py.DiskImage import DiskImage
from d64py.TrackSector import TrackSector
from d64py import Geometry
from d64py.Exceptions import PartialChainException
from d64py.Exceptions import PartialDirectoryException
from d64py.DiskImage import TextLine, LineType

class Analyzer(QObject):
    """
    This class performs an in-depth analysis of a disk image. It runs on its
    own thread and emits progress and finished signals.
    """
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)

    def __init__(self, diskImage: DiskImage):
        super().__init__()
        self.diskImage = diskImage
        self.imageType = diskImage.imageType

    def run(self):
        output = []
        self.anomalies = 0

        message = f"Analyzing {self.diskImage.imagePath.name} (image type: {self.imageType.description})"
        self.progress.emit(message) # parent's listener logs it
        output.append(TextLine(message, LineType.NORMAL))
        message = "  analyzing directory..."
        self.progress.emit(message)
        output.append(TextLine(message, LineType.NORMAL))

        # show directory chain
        dirError = None
        try:
            trackSectors = self.diskImage.followChain(Geometry.getFirstDirTrackSector(self.imageType)).sectors
        except Exception as exc:
            if isinstance(exc, PartialChainException):
                dirChain = exc.getPartialChain()
                trackSectors = dirChain.sectors
                dirError = exc.getMessage()

        index = 0; sectorCount = 0; message = "  "
        while index < len(trackSectors):
            ts = trackSectors[index]
            index += 1
            message += " "
            if index == len(trackSectors) and not dirError is None:
                message += dirError
            sectorCount += 1
            if sectorCount == 8: # show 8 track/sectors per line
                self.progress.emit(message)
                if dirError:
                    output.append(TextLine(message, LineType.ERROR))
                    self.anomalies += 1
                else:
                    output.append(TextLine(message, LineType.NORMAL))
                message = "  "
                sectorCount = 0

        if message.strip():
            self.progress.emit(message)
            if dirError:
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1
            else:
                output.append(TextLine(message, LineType.NORMAL))

        # show directory statistics
        try:
            dirEntries = self.diskImage.getDirectory()
        except PartialDirectoryException as pxc:
            # should be same error from call to followChain() above
            dirEntries = pxc.getPartialDirectory()
        message = f"  directory entries: {len(dirEntries)}"
        blocksUsed = sum(dirEntry.getFileSize() for dirEntry in dirEntries)
        message += f", blocks used (directory total): {blocksUsed} of {Geometry.getMaxBlocksFree(self.imageType)}"
        self.progress.emit(message)
        if blocksUsed > Geometry.getMaxBlocksFree(self.imageType):
            output.append(TextLine(message, LineType.ERROR))
            self.anomalies += 1
        else:
            output.append(TextLine(message, LineType.NORMAL))

        # First pass: get all file chains for duplicate pointer analysis.
        # "chains" will hold a dict of DirEntry --> Chain for sequential files,
        # and DirEntry --> dict: record no. --> Chain for GEOS VLIR files.
        chains = {}
        for dirEntry in dirEntries:
            try:
                if dirEntry.isGeosFile() \
                and dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
                    chains[dirEntry] = self.diskImage.getVlirChains(dirEntry)
                else:
                    chains[dirEntry] = self.diskImage.getChain(dirEntry)
            except PartialChainException as pxc:
                logging.debug(pxc)
                chains[dirEntry] = pxc.getPartialChain()
                continue
            except Exception as exc:
                logging.debug(f"Analyzer 109: {exc}")

        # Second pass: analyze directory entries
        for dirEntry in dirEntries:
            message = '\n"{:16s}" {:4s} '.format(dirEntry.getDisplayFileName(), dirEntry.getFileTypeDescription())
            if dirEntry.isGeosFile():
                message += (f"(GEOS/{dirEntry.getGeosFileType().name}, {dirEntry.getGeosFileStructure().name})")
            else:
                message += "(not GEOS)"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.NORMAL))

            # check file allocation size
            chain = chains.get(dirEntry)
            if not chain:
                message = f"  dir length {dirEntry.getFileSize()}, sector count ???"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1
            else:
                if dirEntry.isGeosFile() \
                and dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
                    # for VLIR files, "chain" is a dict: record no. --> Chain
                    sectorCount = 0
                    for record in list(chain):
                        sectorCount += len(chain[record].sectors)
                else:
                    sectorCount = len(chain.sectors)
                if dirEntry.isGeosFile():
                    sectorCount += 1 # GEOS file header (assuming present and valid)
                    if dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
                        sectorCount += 1   # VLIR index (assuming present and valid)
                message = f"  dir length {dirEntry.getFileSize()}, sector count {sectorCount}"
                self.progress.emit(message)
                if not dirEntry.getFileSize() == sectorCount:
                    output.append(TextLine(message, LineType.ERROR))
                    self.anomalies += 1
                else:
                    output.append(TextLine(message, LineType.NORMAL))

            # analyze GEOS file header if present:
            if dirEntry.isGeosFile():
                self.analyzeGeosHeader(dirEntry, dirEntries, chains, output)

            if not Geometry.isValidTrackSector(dirEntry.getFileTrackSector(), self.imageType):
                message = f"  directory points to invalid track/sector: {dirEntry.getFileTrackSector()}"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1
                continue

            if not chain:
                message = "  Couldn't read chain."
                self.progress.emit(message)
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1
                continue

            # verify that none of this chain's sectors are in another chain
            if dirEntry.isGeosFile() \
            and dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
                # for VLIR files, "chain" is a  dict: VLIR record no. --> Chain
                message = f"  analyzing VLIR chains (index is at {dirEntry.getFileTrackSector()})"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.NORMAL))
                for recordNo in chain.keys():
                    message = f"\n  analyzing VLIR chain {recordNo}"
                    #message = f"<br>  analyzing VLIR chain {recordNo}"
                    self.progress.emit(message)
                    output.append(TextLine(message, LineType.NORMAL))
                    self.analyzeTrackSectors(chain.get(recordNo).sectors, dirEntry, chains, output)
            else:
                # for C= SEQ or GEOS SEQUENTIAL files, "chain" is a Chain
                message = f"  analyzing sequential chain"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.NORMAL))
                self.analyzeTrackSectors(chain.sectors, dirEntry, chains, output)

        message = f"\nDisk analysis complete, {self.anomalies} anomalies encountered."
        self.progress.emit(message)
        # This has to be the last TextLine, as the Wrangler retrieves it for a message box.
        output.append(TextLine(message, LineType.NORMAL))
        self.finished.emit(output)

    # ======================================================================

    def analyzeGeosHeader(self, dirEntry: DirEntry, dirEntries: list, chains: dict, output: list):
        """
        Analyze GEOS file header for invalid pointers.
        :param dirEntry: The DirEntry whose file header is being analyzed.
        :param dirEntries: The list of DirEntrys on the image.
        :param chains: The list of all file chains on the image.
        :param output: The list of strings comprising the analysis output.
        :return: nothing
        """
        message = "  analyzing GEOS header"
        self.progress.emit(message)
        output.append(TextLine(message, LineType.NORMAL))

        ts = dirEntry.getGeosFileHeaderTrackSector()
        if ts is None:
            message = "  no GEOS file header present"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.ERROR))
            self.anomalies += 1
            return

        message = f"  GEOS header: {ts}"

        if not Geometry.isValidTrackSector(ts, self.imageType):
            message += "  (invalid track/sector)"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.ERROR))
            self.anomalies += 1
            return

        # make sure there's no forward pointer
        try:
            buffer = self.diskImage.readSector(ts)
            if buffer[0]: # i.e. if not EOF (forward track pointer is 0)
                fwdPtr = TrackSector(buffer[0], buffer[1])
                message += f"  (forward pointer {fwdPtr}, should be 0/255)"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1
        except Exception as exc:
            logging.exception(exc)
            message += " (error reading header)"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.ERROR))
            self.anomalies += 1
            return

        # Verify no duplicate header pointers.
        for entry in dirEntries:
            if entry == dirEntry:
                continue # don't compare to itself

            # check if the header link is duplicated:
            if ts == entry.getGeosFileHeaderTrackSector():
                message = f"  (duplicate header pointer with {entry.getFileName()})"
                self.progress.emit(message)
                output.append(TextLine(message, LineType.ERROR))
                self.anomalies += 1

            # check against all other file chains
            chainsKeyError = False
            try:
                if chains[entry] and isinstance(chains[entry], Chain): # SEQ, check single chain
                    if ts in chains[entry].sectors:
                        message = f" (header sector appears in data of {entry.getFileName()})"
                        self.progress.emit(message)
                        output.append(TextLine(message, LineType.ERROR))
                        self.anomalies += 1
                else: # VLIR, check all chains
                    vlirChains = chains[entry]
                    for i in vlirChains.keys():
                        vlirChain = vlirChains[i]
                        if ts in vlirChain.sectors:
                            message = f"  (header sector appears in data of {entry.getDisplayFileName()}, record {i}"
                            self.progress.emit(message)
                            output.append(TextLine(message, LineType.ERROR))
                            self.anomalies += 1
            except KeyError as kxc:
                chainsKeyError = True

        if chainsKeyError:
            message = f"  Can't read some chains for checking cross-links!"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.ERROR))
            self.anomalies += 1

    # ======================================================================

    def analyzeTrackSectors(self, trackSectors: list, dirEntry: DirEntry, chains: dict, output: list):
        """
        Make sure none of the given track/sectors are in any other chain.
        :param trackSectors: The sectors to analyze.
        :param dirEntry: The directory entry for the sectors being analyzed.
        :param chains: A dictionary of directory entries to chains.
        :param output: The list of strings comprising the analysis output.
        :return: nothing
        """
        i = 0; sectorCount = 0; message = ""
        errorLines: list[TextLine] = []
        # List track/sectors in chain, showing invalid and cross-linked sectors.
        while i < len(trackSectors):
            thisSector = trackSectors[i]
            message += f"  {thisSector}"
            if not Geometry.isValidTrackSector(thisSector, self.imageType):
                errorMessage = f"{thisSector} (invalid track/sector)"
                errorLines.append(TextLine(errorMessage, LineType.ERROR))
                self.anomalies += 1
            for entry in chains.keys():
                if dirEntry == entry:
                    continue # don't compare with itself
                chain = chains[entry]
                if isinstance(chain, Chain): # C= SEQ or GEOS SEQUENTIAL
                    if thisSector in chain.sectors:
                        errorMessage = f"{thisSector} (cross-link with {entry.getDisplayFileName()})"
                        self.progress.emit(message)
                        output.append(TextLine(message, LineType.ERROR))
                        self.anomalies += 1
                elif isinstance(chain, dict): # GEOS VLIR: record no. -> Chai
                    if not chain.keys():
                        continue # invalid VLIR index pointer, can't check
                    for recordNo in chain.keys():
                        vlirSectors = chain[recordNo].sectors
                        if thisSector in vlirSectors:
                            message = f"(cross-link with {entry.getDisplayFileName()}, record {recordNo})"
                            self.progress.emit(message)
                            output.append(TextLine(message, LineType.ERROR))
                            self.anomalies += 1
            sectorCount += 1
            if sectorCount == 8: # show 8 sectors per line
                self.progress.emit(message)
                output.append(TextLine(message, LineType.NORMAL))
                sectorCount = 0; message = ""
            i += 1

        if sectorCount:
            self.progress.emit(message)
            output.append(TextLine(message, LineType.NORMAL))

        if errorLines:
            message = "\nErrors:"
            self.progress.emit(message)
            output.append(TextLine(message, LineType.NORMAL))
            for line in errorLines:
                self.progress.emit(line.text())
                output.append(TextLine(message, LineType.ERROR))

