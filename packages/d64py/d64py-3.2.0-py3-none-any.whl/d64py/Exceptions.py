#======================================================================
# Exceptions.py
#======================================================================
from d64py.Chain import Chain
from d64py.DirEntry import DirEntry

class GeometryException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class InvalidRecordException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class PartialChainException(Exception):
    partialChain: Chain

    def __init__(self, message: str, partialChain: Chain):
        super().__init__(message)
        self.partialChain = partialChain

    def getPartialChain(self) -> Chain:
        return self.partialChain

class PartialDataException(Exception):
    """
    Exception type for a text file whose chain contains an invalid track and
    sector or a circular reference. The partial data are contained within
    the exception.
    """
    def __init__(self, message: str, partialData: list):
        super().__init__(message)
        self.partialData = partialData

class PartialDirectoryException(Exception):
    partialDir: list[DirEntry]

    def __init__(self, message, partialDir: list[DirEntry]):
        super().__init__(message)
        self.partialDir = partialDir

    def getPartialDir(self) -> list[DirEntry]:
        return self.partialDir

class InsufficientSpaceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
