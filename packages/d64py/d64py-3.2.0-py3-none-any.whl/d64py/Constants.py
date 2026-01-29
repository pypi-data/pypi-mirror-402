#======================================================================
# Constants.py
#======================================================================
from enum import Enum, auto

class ImageType(Enum):
    D64       = ("D64 image", (".d64", ".d41"))
    D64_ERROR = ("D64 error image",(".d64", ".d41"))
    D81       = ("D81 image", (".d81",))

    def __init__(self, description: str, extensions: tuple[str]):
        self.description = description
        self.extensions = extensions

    def description(self) -> str:
        return self.description

    def extensions(self)-> str:
        return self.extensions

class FontOffsets(Enum):
    #GEOS file header font offsets:
    O_GHSETLEN  = 0x61
    O_GHFONTID  = 0x80
    O_GHPTSIZES = 0x82

    # GEOS font header offsets:
    F_BASELN = 0
    F_SETWD  = 1
    F_HEIGHT = 3
    F_INDEX  = 4
    F_DATA   = 6

class ConvertType(Enum):
    CONVERT_NONE       = auto()
    CONVERT_TO_ASCII   = auto()
    CONVERT_TO_PETSCII = auto()

class CharSet(Enum):
    ASCII   = auto()
    PETSCII = auto()

class SectorErrors(Enum):
    NOT_REPORTED          = (0x00, "not reported")
    NO_ERROR              = (0x01, "no error")
    NO_HEADER             = (0x02, "header block not found")
    NO_SYNC               = (0x03, "no sync")
    NO_DATA               = (0x04, "data block not found")
    DATA_CHECKSUM_ERROR   = (0x05, "data checksum error")
    HEADER_CHECKSUM_ERROR = (0x09, "header checksum error")
    ID_MISMATCH           = (0x0b, "disk ID mismatch")
    DRIVE_NOT_READY       = (0x0f, "drive not ready")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    def getSectorErrorDescription(code: int) -> str:
        errorDescription = None

        for sectorError in SectorErrors:
            if code == sectorError.code:
                errorDescription = sectorError.description
        return errorDescription

    def code(self):
        return self.code

    def description(self):
        return self.description

class FileType(Enum):
    FILETYPE_DELETED    = (0, "DEL")
    FILETYPE_SEQUENTIAL = (1, "SEQ")
    FILETYPE_PROGRAM    = (2, "PRG")
    FILETYPE_USER       = (3, "USR")
    FILETYPE_RELATIVE   = (4, "REL")

    def __init__(self, code, abbreviation):
        self.code = code
        self.abbreviation = abbreviation

    def code(self):
        return self.code

    def abbreviation(self):
        return self.abbreviation

class FileStatus(Enum):
    FILE_UNCLOSED    = 0x00
    FILE_NORMAL      = 0x80
    FILE_REPLACEMENT = 0xa0
    FILE_LOCKED      = 0xc0

class GeosFileType(Enum):
    NOT_GEOS     = (0, "NOT GEOS")
    BASIC        = (1, "BASIC")
    ASSEMBLY     = (2, "ASSEMBLY")
    DATA         = (3, "DATA")
    SYSTEM       = (4, "SYSTEM")
    DESK_ACC     = (5, "DESK ACCESSORY")
    APPLICATION  = (6, "APPLICATION")
    APPL_DATA    = (7, "APPLICATION DATA")
    FONT         = (8, "FONT")
    PRINTER      = (9, "PRINTER")
    INPUT_DEVICE = (10, "INPUT DEVICE")
    DISK_DEVICE  = (11, "DISK DEVICE")
    SYSTEM_BOOT  = (12, "SYSTEM BOOT")
    TEMPORARY    = (13, "TEMPORARY")
    AUTOEXEC     = (14, "AUTOEXEC")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    def code(self):
        return self.code

    def description(self):
        return self.description

class GeosFileStructure(Enum):
    SEQUENTIAL = 0
    VLIR = 1

class DirEntryOffsets(Enum):
    DIR_LENGTH = 30

class D64ErrorCodes(Enum):
    NO_ERROR              = (0x01, "no error")
    NO_HEADER             = (0x02, "header block not found")
    NO_SYNC               = (0x03, "no sync")
    NO_DATA               = (0x04, "data block not found")
    DATA_CHECKSUM_ERROR   = (0x05, "data checksum error")
    HEADER_CHECKSUM_ERROR = (0x09, "header checksum error")
    ID_MISMATCH           = (0x0b, "disk ID mismatch")
    DRIVE_NOT_READY       = (0x0f, "drive not ready")

    def __init__(self, errorCode: int, errorMessage: str):
        self.errorCode = errorCode
        self.errorMessage = errorMessage
