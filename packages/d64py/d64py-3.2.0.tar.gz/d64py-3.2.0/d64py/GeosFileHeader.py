#======================================================================
# GeosFileHeader.py
#======================================================================
import logging
from d64py.Constants import FontOffsets
from d64py import D64Utility

class GeosFileHeader:
    def __init__(self, raw: bytearray):
        if not len(raw) == 256:
            raise Exception("File header must be 256 bytes!")
        self.raw = raw
        self.info = self.makeString(raw, 160, 96)

    def getFontId(self) -> int:
        return D64Utility.makeWord(self.raw, FontOffsets.O_GHFONTID.value)
        
    def getPointSizes(self) -> list[int]:
        """
        For a font file, return a list of available point sizes.
        :return: A list of point sizes.
        """
        pointSizes = []

        # the PRG, HHGG, and Boyce are all wrong (15 words, not 16):
        i = 0
        while i < 30:
            fontId = D64Utility.makeWord(self.raw, FontOffsets.O_GHPTSIZES.value + i)
            if fontId:
                pointSize = D64Utility.getPointSize(fontId)
                if pointSize: #ignore Perfect Print LQ info
                    pointSizes.append(pointSize)
            i += 2
        return pointSizes

    def makeString(self, buffer: bytearray, start: int, length: int) -> str:
        """
        Helper function: make an ASCII string from raw PETSCII bytes.
        :param buffer: The buffer containing the string.
        :param start: The starting offset of the string within the buffer.
        :param length: The length of the string.
        :return: An ASCII string.
        """
        b = bytearray()
        for i in range(start, start + length):
            if buffer[i] == 0:
                break
            b.append(buffer[i] & 0x7f)
        return b.decode("ascii", "replace")

    def getIconData(self) -> bytearray:
        """
        Get the file's icon data from the header.
        :return: The icon data.
        """
        return self.raw[5:68]

    def getParentApplicationName(self) -> str:
        """
        Get the file's parent application name.
        :return: The parent application name.
        """
        return self.makeString(self.raw, 117, 20)

    def getPermanentNameString(self) -> str:
        """
        Get the file's permanent name string.
        :return: The permanent name string.
        """
        permanentNameString = self.makeString(self.raw, 77, 20)
        if permanentNameString.strip():
            return permanentNameString
        else:
            return " " * 20

    def getPermanentNameVersion(self) -> str:
        """
        Extract the version number from the permanent name string.
        :return: The version number.
        """
        permanentNameString = self.makeString(self.raw, 77, 20)
        if permanentNameString.strip():
            return permanentNameString[12:16]
        else:
            return " " * 4

    def getInfo(self) -> str:
        """
        Get the file's info block as human-readable text.
        :return: The info block.
        """
        return self.makeString(self.raw, 160, 96)

    def getPlainInfo(self) -> str:
        escapeChars = [14, 15, 18, 19, 24, 25, 26, 27]
        escape: bool = False
        plainInfo: str = ""

        for c in self.getInfo():
            ordc = ord(c)
            if ordc not in escapeChars:
                plainInfo += chr(ordc & 0x7f)
        return plainInfo

    def getRaw(self) -> bytearray:
        """
        Get the raw bytes making up the file header.
        :return: The raw bytes.
        """
        return self.raw

