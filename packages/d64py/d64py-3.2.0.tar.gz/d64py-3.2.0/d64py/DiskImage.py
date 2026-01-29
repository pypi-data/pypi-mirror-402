#======================================================================
# DiskImage.py
#======================================================================
import logging
from enum import Enum, auto
import mmap
from os import access, R_OK
from pathlib import Path
from d64py import Geometry
from d64py.DirEntry import DirEntry, DirEntryOffsets
from d64py.DirHeader import DirHeader
from d64py.GeosFileHeader import GeosFileHeader
from d64py.Chain import Chain
from d64py.Constants import (GeosFileType, GeosFileStructure, CharSet, 
     ConvertType, DirEntryOffsets, FontOffsets, ImageType, SectorErrors)
from d64py.TrackSector import TrackSector
from d64py.Exceptions import (InvalidRecordException, GeometryException,
     InsufficientSpaceException, PartialChainException, PartialDataException, 
     PartialDirectoryException)
from d64py import D64Utility

class DiskImage:
    def __init__(self, imagePath: Path):
        if not imagePath.exists() or not access(imagePath, R_OK):
            raise Exception(f"Can't access {imagePath.name}!")
        self.imagePath = imagePath
        foundType = D64Utility.findImageType(imagePath)
        if foundType is None:
            raise Exception(f"{imagePath.name} is not a valid Commodore disk image.")
        else:
            self.imageType = foundType
        # open and memory-map the image file
        try:
            self.imageFile = imagePath.open("r+b")
        except PermissionError as pxc:
            logging.debug(f"raised pxc: {pxc}")
            raise pxc
        except Exception as exc:
            logging.debug(f"raised exc: {exc}")
            raise exc
        self.mm = mmap.mmap(self.imageFile.fileno(), 0)
        self.bam = bytearray(Geometry.getBamSize(self.imageType))

#-----------------------------------------------------------------------

    def close(self):
        self.mm.close()
        self.imageFile.close()

#-----------------------------------------------------------------------

    def findDirEntry(self, fileName: str, charSet: CharSet):
        """
         Find the directory entry for a given file name. If the charset
         is specified as PETSCII, it's translated to ASCII first.
        :param fileName: The name of the file to find (trimmed ASCII).
        :param charSet: The charset of the name (PETSCII or ASCII).
        :return: The directory entry for the file.
        """
        dirEntry: DirEntry = None

        match charSet:
            case CharSet.PETSCII:
                fileName = D64Utility.asciiToPetsciiString(fileName)
            case CharSet.ASCII:
                pass
            case _:
                raise Exception("Invalid character set!")
        try :
            for entry in self.getDirectory():
                if entry.getDisplayFileName() == fileName:
                    dirEntry = entry
                    break
        except Exception as exc:
            logging.exception(exc)
        if dirEntry is None:
            raise Exception(f"Can't find {fileName}!")
        return dirEntry

#-----------------------------------------------------------------------

    def getDirectory(self) -> list[DirEntry]:
        """
        Get the directory of a Commodore disk image. NOTE: assumes that
        the directory is contained within a single track, and that the first
        directory sector is the lowest numbered one of the directory.
        If the directory contains an invalid sector or circular reference,
        an exception is raised; the available entries are contained within
        the exception and can be retrieved with getPartialDirectory().
        :return: A list of directory entries.
        """
        dirEntries: list[DirEntry] = []
        exc: Exception = None
        geosFileHeader: GeosFileHeader = None
        sector: bytearray
        
        try:
            dirChain = self.followChain(Geometry.getFirstDirTrackSector(self.imageType))
        except PartialChainException as pxc:
            dirChain = pxc.partialChain
            exc = pxc
        for ts in dirChain.sectors:
            sector = self.readSector(ts)
            entry = 0; offset = 2
            while entry < 8: # 8 DirEntrys per sector
                dirBytes = sector[offset : offset + DirEntryOffsets.DIR_LENGTH.value]
                if not dirBytes[0] == 0: # deleted file
                    dirEntry = DirEntry(dirBytes)
                    dirEntries.append(dirEntry)
                    try:
                        geosFileHeader = self.getGeosFileHeader(dirEntry)
                    except Exception:
                        geosFileHeader = None
                    dirEntry.setGeosFileHeader(geosFileHeader)
                entry += 1
                offset += DirEntryOffsets.DIR_LENGTH.value + 2
        if exc:
            raise PartialDirectoryException(str(exc), dirEntries)

        return dirEntries

#-----------------------------------------------------------------------

    def getFileAsText(self, dirEntry: DirEntry, charSet: CharSet, shifted=False, translate=False) -> list['TextLine']:
        """
        Read a sequential file into lines of text split on carriage
        returns. For PETSCII, Characters are converted to Unicode in
        the 0xe000 range (0xe100 if shifted) to use Style's TrueType
        CBM font.
        :param dirEntry: The directory entry of the file.
        :param charSet: The CharSet to use (ASCII or PETSCII).
        :param shifted: For PETSCII, whether to use the shifted
        Commodore character set. Optional parameter.
        :param translate: If PETSCII, whether to translate to ASCII
        (e.g. to save a C= SEQ file). Optional parameter.
        :return: A list of TextLines representing the lines of text.
        """
        trackSectors = []
        fileBuffer = bytearray()

        ts = dirEntry.getFileTrackSector()
        trackSectors.append(ts)
        sectorBuffer = self.readSector(ts)
        moreSectors = True

        while moreSectors:
            if not sectorBuffer[0]: # is there a next sector?
                lastByte = sectorBuffer[1]
                moreSectors = False
            else:
                lastByte = 255
                moreSectors = True
            for i in range(2, lastByte + 1):
                fileBuffer.append(sectorBuffer[i])
            if moreSectors:
                ts = TrackSector(sectorBuffer[0], sectorBuffer[1])
                if not Geometry.isValidTrackSector(ts, self.imageType):
                    raise PartialDataException(f"invalid track and sector: {str(ts)}", self.getTextLines(fileBuffer))
                if ts in trackSectors:
                    raise PartialDataException(f"circular reference: {str(ts)}", self.getTextLines(fileBuffer))
                trackSectors.append(ts)
                sectorBuffer = self.readSector(ts)
        
        if charSet == CharSet.PETSCII:
            lines = []
            line = []
            for i in range(len(fileBuffer)):
                if fileBuffer[i] == 0x0d:
                    strLine = ""
                    for c in line:
                        if translate:
                            try:
                                strLine += chr(D64Utility.petsciiToAsciiChar(int(c)))
                            except Exception as exc:
                                logging.debug(exc)
                                logging.debug(f"strLine: {strLine}, offending char: {int(c)}")
                        else:
                            strLine += chr(c)
                    lines.append(TextLine(strLine, LineType.NORMAL))
                    line = []
                else:
                    if translate:
                        line.append(fileBuffer[i])
                    else:
                        line.append(fileBuffer[i] | 0xe100 if shifted else fileBuffer[i] | 0xe000)
        else: # ASCII
            pageLines = fileBuffer.decode("latin-1").split('\r')
            lines = []
            for line in pageLines:
                lines.append(TextLine(line, LineType.NORMAL))

        return lines

#-----------------------------------------------------------------------

    def makeGeosDisk(self):
        """
        Make this a GEOS disk: allocate off-page directory sector (the
        "border"), add GEOS format string. Note that this method reads the
        BAM and flushes it afterward if no exception is thrown. It's
        assumed that this would not be called during other operations that
        keep a BAM cache.
        :return: nothing
        """
        self.readBam() # cache it

        dirHeaderTs = Geometry.getDirHeaderTrackSector(self.imageType)
        dirHeaderSector = self.readSector(dirHeaderTs)

        # off-page directory sector (border):
        startingTs = TrackSector(Geometry.getDirectoryTrack(self.imageType) + 1, 0)
        borderTs = self.findNextFree(TrackSector(Geometry.getDirectoryTrack(self.imageType) + 1, 0))
        self.allocateSector(borderTs)
        borderSector = self.readSector(borderTs)
        for i in range(Geometry.getSectorSize(self.imageType)):
            borderSector[i] = 0
        borderSector[1] = 0xff # forward pointer 0x00/0xff
        self.writeSector(borderTs, borderSector)
        dirHeaderSector[171] = borderTs.track # same for D64 and D81
        dirHeaderSector[172] == borderTs.sector

        # GEOS format string:
        geosFormat = "GEOS format V1.0"
        for i in range(len(geosFormat)):
            dirHeaderSector[173 + i] = ord(geosFormat[i])
        self.writeSector(dirHeaderTs, dirHeaderSector)
        self.writeBam() # flush cache

#-----------------------------------------------------------------------

    def getGeoWriteFileAsLines(self, dirEntry: DirEntry) -> list[list['TextLine']]:
        """
        Read a geoWrite file and parse into pages of lines. Escape
        sequences are stripped. Both geoWrite 2.0 page format (records
        0-60 are text pages and 61-63 are header/footer data) and
        earlier (0-63 are text pages) are supported, as well as the
        earlier type of ruler escape.
        :param dirEntry: The directory entry of the geoWrite file.
        :return: A list of lists of TextLines, each representing the lines of a page.
        """
        partialData = False
        pages = [] # list of lists of TextLine
        pageBuffer = bytearray() # characters in page

        appVersion = self.getGeosFileHeader(dirEntry).getPermanentNameVersion()
        vlirIndex= self.readSector(dirEntry.getFileTrackSector())
        if appVersion < "V2":
            # ignore t/s pointer, records > 63
            lastIndex = 128
        else:
            # ignore t/s pointer, records > 68
            lastIndex = 122

        index = 2
        while index < lastIndex: # walk through VLIR records (pages)
            if not vlirIndex[index]:
                break # no more pages
            partialPage = False
            ts = TrackSector(vlirIndex[index], vlirIndex[index + 1])
            if not Geometry.isValidTrackSector(ts, self.imageType):
                logging.debug(f"\n*** CAN'T READ PAGE {int(index / 2)} ***")
                textLines = [TextLine(f"\n*** CAN'T READ PAGE {int(index / 2)} ***\n", LineType.ERROR)]
                pages.append(textLines)
                index += 2
                continue
            sectorBuffer = self.readSector(ts)
            firstSector = True

            # Read entire page into a single string for split. It may
            # seem wasteful not to use readVlirRecord(), but you'd still
            # have to remove the escapes and move back subsequent data.
            overflow = 0; moreSectors = True
            while moreSectors:
                if not sectorBuffer[0]:
                    lastByte = sectorBuffer[1]
                    # Horrible kludge because I don't know why
                    # a geoWrite page sometimes ends with a $00 byte:
                    if not sectorBuffer[lastByte]:
                        if lastByte > 2: # only one byte in sector?
                            lastByte -= 1
                        else:
                            sectorBuffer[lastByte] = 0x0d
                    moreSectors = False
                else:
                    lastByte = 255
                    moreSectors = True

                if firstSector and appVersion < "V2":
                    start = 22 # bypass old-style ruler escape
                else:
                    start = 2  # starting offset (after t/s pointer)
                firstSector = False

                if overflow:
                    start += overflow # remainder of escape from previous sector
                    overflow = 0
                i = start
                while i <= lastByte:
                    match(sectorBuffer[i]):
                        case 0x0c:  # page break
                            i += 1
                        case 0x10:  # graphics escape
                            i += 4  # 5 bytes
                        case 0x11:  # ruler escape
                            i += 26 # 27 bytes
                        case 0x17:  # font escape
                            i += 3  # 4 bytes
                        case _:
                            pageBuffer.append(sectorBuffer[i])
                    if i > lastByte:
                        overflow = i - lastByte
                    i += 1

                if sectorBuffer[0]:
                    ts = TrackSector(sectorBuffer[0], sectorBuffer[1])
                    if not Geometry.isValidTrackSector(ts, self.imageType):
                        partialPage = True
                        partialData = True
                        moreSectors = False
                    else:
                        sectorBuffer = self.readSector(ts)
            # end of inner loop (walk through sectors in VLIR record)
            try:
                pageLines = pageBuffer.decode(encoding="utf-8", errors="replace").split('\r')
            except Exception as exc:
                logging.exception(exc)
            textLines = []
            for line in pageLines:
                textLines.append(TextLine(line, LineType.NORMAL))
            pageBuffer = bytearray() # clear

            if partialPage:
                textLines.append(TextLine(f"\r*** PARTIAL DATA ON PAGE {int(index / 2)} ***\r", LineType.ERROR))
                partialPage = False
            pages.append(textLines)

            index += 2
        # end of outer loop (walk through VLIR records)

        if partialData:
            raise PartialDataException("Not all data could be read from this file.", pages)
        return pages

#-----------------------------------------------------------------------

    def getTextAlbumAsPages(self, dirEntry: DirEntry) -> list[list['TextLine']]:
        vlirIndex = diskImage.getGeosVlirIndex(dirEntry)
        version = dirEntry.getGeosFileHeader().getPermanentNameVersion()
        logging.info(f"text album {dirEntry.getDisplayFileName()} is version {version}")
        if version == "V2.1": # supports named scraps
            record = 0; namesRecordNo = -1
            while record < 127: # find last record (contains names)
                offset = (record + 1) * 2  # convert VLIR record no. to sector index
                if not index[offset]:
                    if record > 0:
                        namesRecordNo = record - 1 
                        namesRecord = diskImage.readVlirRecord(namesRecordNo, dirEntry)
                        break
                record += 1

        pages = [] # list of lists of TextLine
        pageBuffer = bytearray() # characters in page
        index = 2
        while index < 256: # walk through VLIR records (pages)
            if not vlirIndex[index]:
                break # no more pages
            ts = TrackSector(vlirIndex[index], vlirIndex[index + 1])
            if not Geometry.isValidTrackSector(ts, self.imageType):
                textLines = [TextLine(f"\n*** CAN'T READ PAGE {int(index / 2)} ***\n", LineType.ERROR)]
                pages.append(textLines)
                continue
                
            data = self.readChain(ts)
            textBuffer = bytearray()
            i = 2 # past length bytes
            while i < len(data):
                match(data[i]):
                    case 0x0c:  # page break
                        i += 1
                    case 0x10:  # graphics escape
                        i += 4  # 5 bytes
                    case 0x11:  # ruler escape
                        i += 26 # 27 bytes
                    case 0x17:  # font escape
                        i += 3  # 4 bytes
                    case _:
                        textBuffer.append(data[i])
                        i += 1
            try:
                scrapLines = textBuffer.decode(encoding="utf-8", errors="replace").split('\r')
            except Exception as exc:
                logging.exception(exc)
            textLines = []
            for line in scrapLines:
                textLines.append(TextLine(line, LineType.NORMAL))
            pages.append(textLines)
            index += 2
        return pages
        
#-----------------------------------------------------------------------

    def getTextScrapAsText(self, dirEntry: DirEntry) -> list['TextLine']:
        """
        Read a text scrap and parse into lines. Escape sequences are
        stripped.
        :param dirEntry: The directory entry of the text scrap.
        :return: A list of lists of TextLines, each representing the lines of a page.
        """
        ts = dirEntry.getFileTrackSector()
        data = self.readChain(ts)
        textBuffer = bytearray()
        i = 2 # past length bytes
        while i < len(data):
            match(data[i]):
                case 0x0c:  # page break
                    i += 1
                case 0x10:  # graphics escape
                    i += 4  # 5 bytes
                case 0x11:  # ruler escape
                    i += 26 # 27 bytes
                case 0x17:  # font escape
                    i += 4  # 4 bytes
                case _:
                    textBuffer.append(data[i])
                    i += 1
        try:
            scrapLines = textBuffer.decode(encoding="utf-8", errors="replace").split('\r')
        except Exception as exc:
            logging.exception(exc)
        textLines = []
        for line in scrapLines:
            textLines.append(TextLine(line, LineType.NORMAL))
        return textLines

#-----------------------------------------------------------------------

#def streamGeosFileAsCvt(dirEntry: DirEntry, path: Path): # FIXME

###from SO: (this will be for geoGopher)
#from django.core.files.base import ContentFile
#def your_view(request):
#    #your view code
#    string_to_return = get_the_string() # get the string you want to return.
#    file_to_send = ContentFile(string_to_return)
#    response     = HttpResponse(file_to_send,'application/x-gzip')
#    response['Content-Length']      = file_to_send.size    
#    response['Content-Disposition'] = 'attachment; filename="somefile.tar.gz"'
#    return response   

#-----------------------------------------------------------------------

    def getMegaFontPointSize(self, dirEntry: DirEntry, fileHeader: GeosFileHeader):
        """
        Get the true point size of a mega font. If the font headers contain more
        than one character height, only the first is returned, and a warning is
        written to the log.
        :param dirEntry: The directory entry of the font file.
        :param fileHeader: The GEOS file header of the font file.
        :return: The true point size (character height in pixels) of the mega font.
        """
        pointSize = 0

        if not self.isMegaFont(dirEntry, fileHeader):
            raise Exception(f"{dirEntry.getDisplayFileName()} is not a mega font!")
        megaFontData = self.readMegaFontData(dirEntry)
        for i in megaFontData.keys():
            if not pointSize:
                pointSize = megaFontData.get(i)[FontOffsets.F_HEIGHT.value]
            else:
                logging.warning(f"mega font {dirEntry.getDisplayFileName()} has multiple heights in font headers!")
        return pointSize

#-----------------------------------------------------------------------

    def readMegaFontData(self, dirEntry: DirEntry) -> dict:
        """
        Read the VLIR records of a GEOS mega font.
        :param dirEntry: The file's directory entry.
        :return: A dictionary of record numbers to VLIR records.
        """
        megaFontData = {}
        for i in range(48, 55):
            megaFontData[i] = self.readVlirRecord(i, dirEntry)
        return megaFontData

#-----------------------------------------------------------------------

    def isMegaFont(self, dirEntry: DirEntry, fileHeader: GeosFileHeader) -> bool:
        """
        Determine whether a GEOS font is a mega font. Both the existence of the
        expected point sizes and the lack of a bitstream in record 54 are
        checked for.
        :param dirEntry: The directory entry of the font file.
        :param fileHeader: The GEOS file header of the font file.
        :return: True if a GEOS mega font, false otherwise.
        """
        megaPointSizes = [48, 49, 50, 51, 52, 53, 54]
        megaPoints = False

        if not dirEntry.isGeosFile():
            return False
        if not dirEntry.getGeosFileType() == GeosFileType.FONT:
            return False
        # Does it have the expected VLIR records?
        pointSizes = fileHeader.getPointSizes()
        if len(pointSizes) == len(megaPointSizes):
            megaPoints = True
            for i in range(len(megaPointSizes)):
                if not megaPointSizes[i] == pointSizes[i]:
                    megaPoints = False
                    break
        if not megaPoints:
            return False

        # A mega font has no bitstream data in record 54,
        # i.e. F_DATA points to the end of the record.
        megaRecord = self.readVlirRecord(54, dirEntry)
        return len(megaRecord) == D64Utility.makeWord(megaRecord, FontOffsets.F_DATA.value)

#-----------------------------------------------------------------------

    def readVlirRecord(self, record: int, dirEntry: DirEntry) -> bytearray:
        """
        Read a record from a GEOS VLIR file.
        :param record: The record number to read.
        :param dirEntry: The file's directory entry.
        :return: The VLIR record's data.
        """
        vlirIndex = self.getGeosVlirIndex(dirEntry)
        index = (record + 1) * 2 # convert record no. to sector index
        ts = TrackSector(vlirIndex[index], vlirIndex[index + 1])
        if ts.isEof():
            raise InvalidRecordException(f"Attempt to read deleted record #{record}")
        return self.readChain(ts)

#-----------------------------------------------------------------------

    def getGeosVlirIndex(self, dirEntry: DirEntry) -> bytearray:
        """
        Get the VLIR index of a file.
        :param dirEntry: The file's directory entry.
        :return: The VLIR index.
        """
        if not dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
            raise Exception("Not a VLIR file!")
        # VLIR directory entry points to its index
        return self.readSector(dirEntry.getFileTrackSector())

#-----------------------------------------------------------------------

    def getGeosFileHeader(self, dirEntry: DirEntry) -> GeosFileHeader:
        """
        Get the GEOS file header for a given directory entry.
        :param dirEntry: The directory entry.
        :return: The file's GEOS header.
        """
        ts: TrackSector
        buffer: bytearray

        ts = dirEntry.getGeosFileHeaderTrackSector()
        if ts.track == 0: # probably a non-GEOS file
            return None
        if not Geometry.isValidTrackSector(ts, self.imageType):
            msg: str = f"{dirEntry.getDisplayFileName()}: invalid track/sector for GEOS file header ({ts})"
            raise GeometryException(msg)
        buffer = self.readSector(ts)
        return GeosFileHeader(buffer)

#-----------------------------------------------------------------------

    def isGeosImage(self) -> bool:
        """
        Determine whether this image is a GEOS disk by looking for the
        signature "GEOS" at bytes 173-176 in the header. Note that many
        disks with GEOS files on them are not actually GEOS disks.
        :return: True if the image is of a GEOS disk, false otherwise.
        """
        ts = Geometry.getDirHeaderTrackSector(self.imageType)
        buffer = self.readSector(ts)
        return buffer[173:177] == "GEOS"

#-----------------------------------------------------------------------

    def getDirHeader(self):
        """
        Get the directory header of this disk image.
        :return: The directory header.
        """
        ts = Geometry.getDirHeaderTrackSector(self.imageType)
        return DirHeader(self.readSector(ts), self.imageType)

#-----------------------------------------------------------------------

    def convertSector(self, sector: bytearray, convertType: ConvertType) -> bytearray:
        """
        Convert a sector buffer from PETSCII to ASCII or vice versa.
        :param sector: The sector buffer.
        :param convertType: Which conversion to do.
        :return: The sector buffer.
        """
        for i in range(2, 256):
            match(convertType):
                case ConvertType.CONVERT_TO_ASCII:
                    sector[i] = D64Utility.petsciiToAscii(sector[i])
                case ConvertType.CONVERT_TO_PETSCII:
                    sector[i] = D64Utility.asciiToPetscii(sector[i])
        return sector

#-----------------------------------------------------------------------

# def deleteFile(dirEntry: DirEntry) # FIXME
# def updateDirEntry(dirEntry: DirEntry) # FIXME

#-----------------------------------------------------------------------

    def getChain(self, dirEntry: DirEntry) -> Chain:
        """
        Get the chain of tracks and sectors used by a file on disk.
        To get the list of chains in a VLIR file, call getVlirChains().
        :param dirEntry: The directory entry of the file.
        :return: A Chain object, which will be empty if the chain cannot
                 be read or incomplete in the case of a PartialChainException.
        """
        if dirEntry.isGeosFile() \
        and dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
            raise GeometryException("Use getVlirChains() for VLIR files.")

        fileTrackSector = dirEntry.getFileTrackSector()
        if not Geometry.isValidTrackSector(fileTrackSector, self.imageType):
            raise Exception(f"dirEntry points to invalid TrackSector: {fileTrackSector}")
        return self.followChain(dirEntry.getFileTrackSector())

#-----------------------------------------------------------------------

    def getVlirChains(self, dirEntry: DirEntry) -> dict:
        """
        Get the list of track and sector chains for a VLIR file.
        :param dirEntry: The file's directory entry.
        :return: A dictionary: VLIR record no. --> sector chain
        """
        # validate each chain (127 records numbered 0 to 126)
        index = 0
        record = 0
        chains: dict = {}  # DirEntry --> Chain or list of Chains (for VLIR files)
        partialVlir = False

        if not dirEntry.isGeosFile():
            raise GeometryException("Not a GEOS file!")
        if not dirEntry.getGeosFileStructure() == GeosFileStructure.VLIR:
            raise GeometryException("Use getChain() for SEQUENTIAL files.")

        vlirIndex = self.readSector(dirEntry.getFileTrackSector())
        while record < 127:
            index = (record + 1) * 2
            if vlirIndex[index] == 0: # no record
                record += 1
                continue
            else:
                ts = TrackSector(vlirIndex[index], vlirIndex[index + 1])
                try:
                    vlirChain = self.followChain(ts)
                    chains[record] = vlirChain
                except PartialChainException as pxc:
                    partialVlir = True
                    chains[record] = pxc.getPartialChain()
            record += 1

        if partialVlir:
            raise PartialChainException("One or more records in this VLIR file are incomplete.", \
                  pxc.partialChain)
        return chains

#-----------------------------------------------------------------------

    def readChain(self, ts: TrackSector) -> bytearray:
        """
        Read the data in a chain of sectors given the starting track and sector.
        :param ts: The first track/sector in the chain.
        :return: The data in the chain as a bytearray.
        """
        chain = self.followChain(ts)
        data = bytearray()
        for trackSector in chain.sectors:
            sector = self.readSector(trackSector)
            if sector[0] == 0:
                try:
                    data.extend(sector[2:sector[1] + 1])
                except Exception as exc:
                    logging.error(exc)
                    raise exc
            else:
                data.extend(sector[2:])
        return data

#-----------------------------------------------------------------------

    def followChain(self, ts: TrackSector) -> Chain:
        """
        Get the chain of sectors starting at a given track and sector. If an
        invalid track/sector or circular reference is encountered, an
        PartialChainException is raised, and the incomplete chain can be
        retrieved from the exception with getPartialChain().
        :param ts: The track and sector that starts the chain.
        :return: A Chain.
        """
        trackSectors:list[TrackSector] = []

        while True:
            if ts in trackSectors:
                msg = f"Circular reference: {ts}"
                raise PartialChainException(msg, Chain(trackSectors))
            trackSectors.append(ts)
            try:
                buffer = self.readSector(ts)
            except Exception as exc:
                raise PartialChainException(str(exc), Chain(trackSectors))
            ts = TrackSector(buffer[0], buffer[1])
            if not ts.isEof() and not Geometry.isValidTrackSector(ts, self.imageType):
                msg = f"Invalid track/sector: {ts}"
                raise PartialChainException(msg, Chain(trackSectors))
            if ts.isEof():
                break
        return Chain(trackSectors)

#-----------------------------------------------------------------------

    def readSector(self, ts: TrackSector) -> bytearray:
        """
        Read a given track and sector from disk image.
        :param ts: The track and sector to be read.
        :return: The sector data as a bytearray.
        """
        offset = Geometry.getSectorByteOffset(ts, self.imageType)
        sector = self.mm[offset : offset + Geometry.getSectorSize(self.imageType)]
        return bytearray(sector) # make editable

#-----------------------------------------------------------------------

    def writeSector(self, ts: TrackSector, sectorBuffer: bytearray):
        """
        Write a given track and sector from a buffer.
        :param ts: The track and sector to be written.
        :param sectorBuffer: The buffer to write.
        :return: Nothing.
        """
        sectorSize = Geometry.getSectorSize(self.imageType)
        if not len(sectorBuffer) == sectorSize:
            msg = f"Expected buffer of length {sectorSize}, got {len(sectorBuffer)}"
            raise Exception(msg)
        offset = Geometry.getSectorByteOffset(ts, self.imageType)
        memoryview(self.mm)[offset:offset + Geometry.getSectorSize(self.imageType)] = sectorBuffer

#-----------------------------------------------------------------------

    def dumpBam(self, imageType: ImageType) -> list[str]:
        """
        Get a traditionally-formatted BAM dump of a disk image. The BAM must 
        first have been read with readBam(). The first two lines are the 
        sector number header, with the remaining lines made up of the track 
        numbers and X/O BAM display. The BAM for a single track can be 
        retrieved with lines.get(track + 1).
        :return: list[DirEntry]
        """
        lines = []
       
        # sector number headers at top
        line = "  "
        # track 1 will always have the maximum number of sectors
        for sector in range(Geometry.getMaxSector(imageType, 1) + 1):
            line += f"{sector:02}"[0:1]
        lines.append(line)

        line = "  "
        for sector in range(Geometry.getMaxSector(imageType, 1) + 1):
            line += f"{sector:02}"[1:2]
        lines.append(line)
        
        # track numbers at left w/allocation status aligned under sector
        for track in range(1, Geometry.getMaxTrack(imageType) + 1):
            line = ""
            line += f"{track:02}"
            for sector in range(Geometry.getMaxSector(imageType, track) + 1):
                line += 'X' if self.isSectorAllocated(TrackSector(track, sector)) else 'O'
            lines.append(line)

        return lines;

#-----------------------------------------------------------------------

    def readBam(self):
        """
        Read the BAM (block availability map) of this disk image. Note
        that only the BAM itself is returned (not the rest of the
        directory header). The BAM is cached at self.bam; writeBam()
        must be called to flush it.
        :return: Nothing.
        """
        bamSize = Geometry.getBamSize(self.imageType)
        match(self.imageType):
            case ImageType.D64 | ImageType.D64_ERROR:
                sectorBuffer = self.readSector(TrackSector(18, 0))
                self.bam = sectorBuffer[4 : (bamSize + 4)]

            case ImageType.D81:
                sectorBuffer = self.readSector(TrackSector(40, 1))
                self.bam[ : int(bamSize / 2)] = sectorBuffer[16 : (16 + int(bamSize / 2))]
                sectorBuffer = self.readSector(TrackSector(40, 2))
                self.bam[int(bamSize / 2) : ] = sectorBuffer[16 : (16 + int(bamSize / 2))]

#-----------------------------------------------------------------------

    def writeBam(self):
        """
        Write the cached BAM (block availability map) back to a disk image.
        :return: Nothing.
        """
        bamSize = Geometry.getBamSize(self.imageType)
        match(self.imageType):
            case ImageType.D64 | ImageType.D64_ERROR:
                ts = TrackSector(18, 0)
                sectorBuffer = self.readSector(ts)
                sectorBuffer[4:4 + bamSize] = self.bam[:]
                self.writeSector(ts, sectorBuffer)
            case ImageType.D81:
                halfBam = int(bamSize / 2)
                ts = TrackSector(40, 1)
                sectorBuffer = self.readSector(ts)
                sectorBuffer[16:16 + halfBam] = self.bam[:halfBam]
                self.writeSector(ts, sectorBuffer)
                ts = TrackSector(40, 2)
                sectorBuffer = self.readSector(ts)
                sectorBuffer[16:16 + halfBam] = self.bam[halfBam:]
                self.writeSector(ts, sectorBuffer)

#-----------------------------------------------------------------------

    def findNextFree(self, ts: TrackSector = TrackSector(1, 0)) -> TrackSector:
        """
        Find the next available sector given a starting point. When no starting 
        point is given, start from track 1, sector 0. Based on the GEOS disk 
        drivers.
        :param  ts The track and sector to begin searching from.
        :return The allocated track and sector (in case another is needed).
        """
        allocatedTrackSector: TrackSector = None
    
        if not Geometry.isValidTrackSector(ts, self.imageType):
            raise GeometryException("findNextFree(): invalid track/sector: " + str(ts))
        
        match self.imageType:
            case ImageType.D64:
                allocatedTrackSector = self.findNextFreeD64(ts)        
            case ImageType.D64_ERROR:
                allocatedTrackSector = self.findNextFreeD64(ts)        
            case ImageType.D81:
                allocatedTrackSector = self.findNextFreeD81(ts)
        return allocatedTrackSector

#-----------------------------------------------------------------------

    def findNextFreeD64(self, ts: TrackSector) -> TrackSector:
        freeTrackSector: TrackSector = None
        findingTrack: bool = True
        backtracking: bool = False
        
        logging.debug(f"findNextFreeD64({ts})")
        startTrack = ts.track;
        startSector = ts.sector;        
        interleave = 8;
        targetTrack = startTrack;
        targetSector = startSector;
        
        while findingTrack:
            logging.debug(f"targetTrack is {targetTrack}, backtracking = {backtracking}")
            if targetTrack > Geometry.getMaxTrack(self.imageType):
                logging.debug(f"too many tracks, bailing")
                raise InsufficientSpaceException("Not enough space on image!")
                
            maxSector = Geometry.getMaxSector(self.imageType, targetTrack)
            if self.getFreeSectorsOnTrack(targetTrack) > 0:
                sectorCounter = maxSector + 1
                findingSector = True
                while findingSector:
                    if self.isSectorAllocated(TrackSector(targetTrack, targetSector)):
                        logString = f"{targetTrack}/{targetSector} is allocated... "  
                        if targetSector == maxSector:
                            targetSector = 0
                            logString += f"(was max, now {targetTrack}/{targetSector})"
                            logging.debug(logString)
                        else:
                            targetSector += 1 # ignore interleave on retry
                            if targetSector > maxSector:
                                targetSector -= maxSector
                            logString += f"(adjusted for interleave: {targetSector})"
                        sectorCounter -= 1
                        logging.debug(f"sectorCounter: {sectorCounter}")
                        if sectorCounter == 0:
                            logging.debug(f"all sectors on track {targetTrack} allocated, next track") 
                            findingSector = False
                            targetTrack += 1
                    else:
                        freeTrackSector = TrackSector(targetTrack, targetSector)
                        logging.debug(f"freeTrackSector created: {freeTrackSector}")
                        if not Geometry.isValidTrackSector(freeTrackSector, self.imageType):
                            logging.debug(f"OOPS!!! findNextFreeD64({ts}) returns {freeTrackSector} ")
                            raise GeometryException(f"*** findNextFreeD64({ts}) created a monster: {freeTrackSector} ***")
                        findingSector = False
                        findingTrack = False
                
            else: # target track is full, try next track
                if targetTrack == 18: # can only happen at the beginning
                    raise InsufficientSpaceException("Not enough space in directory!")
                targetTrack += 1
                # Allow starting from directory track, but if it comes up on an
                # increment, skip it.
                if targetTrack == 18:
                    targetTrack += 1
                if backtracking and targetTrack == startTrack:
                    logging.debug("backtracking, wrapped around")
                    raise InsufficientSpaceException("Not enough space on disk!");
                if  targetTrack > Geometry.getMaxTrack(self.imageType):
                    # Since the 1541 driver only steps tracks outward, we have to
                    # backtrack to track 1 to make sure we didn't miss anything.
                    # See SetNextFree commentary in Hitchhiker's Guide To GEOS.
                    if startTrack > 1:
                        targetTrack = 1
                        targetSector = 0
                        logging.debug(f"1/0, backtracking")
                        backtracking = True # ignore head settle calculation

        return freeTrackSector

#-----------------------------------------------------------------------

    def findNextFreeD81(self, ts: TrackSector) -> TrackSector:
        freeTrackSector: TrackSector = None
        findingTrack: bool = True
        findingSector: bool = False
        tried39: bool = False
    
        startTrack = ts.track
        startSector = ts.sector
        targetTrack = startTrack;
        targetSector = startSector + 1 # no interleave on a 1581

        while findingTrack:
            maxSector = Geometry.getMaxSector(self.imageType, targetTrack)
            if self.getFreeSectorsOnTrack(targetTrack) > 0:
                sectorCounter = maxSector + 1
                findingSector = True
                while findingSector:
                    while targetSector > maxSector:
                        targetSector -= maxSector + 1
                    if self.isSectorAllocated(TrackSector(targetTrack, targetSector)):
                        targetSector += 1
                        sectorCounter -= 1
                        if sectorCounter == 0:
                            findingSector = false  # next track
                    else:
                        freeTrackSector = TrackSector(targetTrack, targetSector)
                        findingSector = False
                        findingTrack = False
            
            else: # target track is full, try next track
                if targetTrack == 40: # can only happen at the beginning
                    raise InsufficientSpaceException("Not enough space in directory!")
                if targetTrack >= 41: # allocate tracks outward from directory
                    targetTrack += 1
                elif targetTrack == 40:
                    # Allow starting from directory track, but if it comes up on an
                    # increment, skip it.
                    targetTrack = 41
                else:
                    targetTrack -= 1
                    if targetTrack == 0:
                        targetTrack = 41
                if targetTrack > Geometry.getMaxTrack(self.imageType):
                    # Allocating in both directions from the directory can leave us 
                    # with a hole in the middle. This fixes that; it's in the GEOS 
                    # 1581 driver at the very beginning of SetNextFree.
                    if tried39:
                        raise InsufficientSpaceException("Not enough space on disk!")
                    else:
                        targetTrack = 39
                        tried39 = True
                targetSector = 0
        
        return freeTrackSector
        
#-----------------------------------------------------------------------

    def getBlocksFree(self) -> int:
        blocksFree = 0; track = 1

        while track <= Geometry.getMaxTrack(self.imageType):
            if not track == Geometry.getDirectoryTrack(self.imageType):
                blocksFree += self.getFreeSectorsOnTrack(track)
            track += 1
        return blocksFree

#-----------------------------------------------------------------------

    def getFreeSectorsOnTrack(self,track: int):
        bamTrackBytes = Geometry.getBamBytesPerTrack(self.imageType)
        bamFreeOffset = (track - 1) * bamTrackBytes
        return self.bam[bamFreeOffset]

#-----------------------------------------------------------------------

    def isSectorAllocated(self, ts: TrackSector) -> bool:
        bamTrackBytes = Geometry.getBamBytesPerTrack(self.imageType)
        bamTrackOffset = ((ts.track - 1) * bamTrackBytes) + 1
        bamSectorByte = self.bam[bamTrackOffset + (ts.sector // 8)]
        bamSectorMask = 1 << (ts.sector % 8)
        # bit set means block free, bit clear means allocated
        return not (bamSectorByte & bamSectorMask == bamSectorMask)

#-----------------------------------------------------------------------

    def allocateSector(self, ts: TrackSector):
        """
        Allocate a sector in the BAM. The BAM must first have been cached 
        by calling readBam(). The BAM is not checked to see if the sector 
        is already allocated, and must be flushed afterward by calling 
        writeBam().
        :param  ts The track and sector to allocate.
        """
        bamTrackBytes = Geometry.getBamBytesPerTrack(self.imageType)
        bamTrackOffset = ((ts.track - 1) * bamTrackBytes) + 1
        bamSectorByte = self.bam[bamTrackOffset + int(ts.sector / 8)]
        bamSectorMask = (1 << (ts.sector % 8)) & 0xff
        bamSectorByte &= ~bamSectorMask; # bit clear means sector allocated
        self.bam[bamTrackOffset + int(ts.sector / 8)] = bamSectorByte;
        self.bam[bamTrackOffset - 1] -= 1;    # free sectors on track
        
#-----------------------------------------------------------------------

    def freeSector(self, ts: TrackSector):
        """
        Free a sector in the BAM. The BAM must first have been cached by 
        calling readBam(). The BAM is not checked to see if the sector is 
        already free, and must be flushed afterward by calling writeBam().
        :param  ts The track and sector to free.
        """
        bamTrackBytes = Geometry.getBamBytesPerTrack(imageType)
        bamTrackOffset = ((ts.track - 1) * bamTrackBytes) + 1
        bamSectorByte = self.bam[bamTrackOffset + (ts.sector / 8)]
        bamSectorMask = 1 << (ts.sector % 8) # (byte)
        bamSectorByte |= bamSectorMask; # bit set means sector free
        self.bam[bamTrackOffset + (ts.sector / 8)] = bamSectorByte
        self.bam[bamTrackOffset - 1] += 1; # free sectors on track
        
#-----------------------------------------------------------------------

    def getSectorErrorMap(self) -> dict:
        """
        For a D64 error image, get the map of sectors and their reported errors.
        :return: A dictionary of TrackSector objects to FDC error codes.
        """
        if not self.imageType == ImageType.D64_ERROR:
            raise Exception("Only D64_ERROR images have an error map.")
        errorMap = {}
        errorBytes = bytearray(self.mm[Geometry.getErrorOffset(self.imageType):])
        if not len(errorBytes) == 683:
            raise Exception("D64 error image corrupt!")
        for i in range(0, 683): # no. sectors in a D64
            errorMap[Geometry.getOffsetSector(i, self.imageType)] = errorBytes[i]
        return errorMap

#-----------------------------------------------------------------------

    def getSectorErrorCode(self, ts: TrackSector) -> int:
        if not (self.imageType == ImageType.D64_ERROR):
            raise Exception("Not a D64 error image!")
        return Geometry.getErrorOffset(self.imageType) \
             + Geometry.getSectorOffset(ts, self.imageType)

#-----------------------------------------------------------------------

    def getSectorErrorDescription(self, code: int) -> str:
        errorDescription = None
        sectorErrorMap = self.getSectorErrorMap()
        for ts in sectorErrorMap: # key is a TrackSector
            if code == sectorErrorMap[ts]:
                errorDescription = SectorErrors.getSectorErrorDescription(code)
        return errorDescription

# ======================================================================

class LineType(Enum):
    NORMAL  = auto()
    ERROR   = auto()
    HEADING = auto()

class TextLine:
    def __init__(self, text: str, lineType: LineType):
        self.text = text
        if not isinstance(lineType, LineType):
            raise Exception(f"Invalid LineType, text: {text}")
        self.lineType = lineType

    def text(self):
        return self.text

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text
