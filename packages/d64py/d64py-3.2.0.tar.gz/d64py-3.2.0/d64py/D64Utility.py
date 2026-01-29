#======================================================================
# D64Utility.py
#======================================================================
from pathlib import Path
import d64py.Geometry
from d64py.Constants import ImageType, FontOffsets
import logging
import traceback

def getImageSuffixes() -> list[str]:
    """
    Return a list of all image type suffixes.
    :return: The list of suffixes.
    """
    suffixes = []
    for imageType in ImageType:
        for extension in imageType.extensions:
            suffixes.append(extension)
    return suffixes

def findImageType(imagePath: Path) -> ImageType:
    """
    Given a path to a file, verify that it's a disk image
    and return its image type.
    :param imagePath: The path to the file.
    :return: The image type.
    """
    imageType = None
    imageName = imagePath.name
    if len(imageName) < 5 or imageName[len(imageName)- 4] != '.':
        raise Exception("Bad image name: " + imageName)
    suffix = imageName[len(imageName) - 4:]
    for type in ImageType:
        if suffix.lower() in type.extensions:
            if d64py.Geometry.imageLength(type) == imagePath.stat().st_size:
                imageType = type
                break
    if imageType is None:
        raise Exception(f"{imagePath.name} is not a valid Commodore disk image.")
    return imageType

def petsciiToAsciiString(fromStr: str) -> str:
    """
    Convert a PETSCII string to ASCII.
    :param fromStr: The PETSCII string.
    :return: The string translated to ASCII.
    """
    toStr: str = ""

    for c in fromStr:
        toStr += chr(petsciiToAsciiChar(int(c)))
    return toStr

def petsciiToAsciiChar(fromChar: int) -> int:
    """
    Convert a single PETSCII character to ASCII.
    :param fromChar: The character to be convert.
    :return: The converted ASCII character.
    """
    if fromChar < 0x41: # numbers, punctuation, control chars
        if fromChar == 0x0d:
            return 0x0a
        else:
            return fromChar
    if fromChar <= 0x5a: # 'a' - 'z'
        return fromChar | 0x20
    match(fromChar):
        case 0x5c:
            return "\\"
        case 0xa0:
            # return ' '
            return 0x20 # Why is that a problem?
        case 0xa4:
            return '_'
        case 0xaf:
            return '~'
    if fromChar < 0xc1: # other punctuation
        return fromChar
    if fromChar <= 0xda: # 'A' - 'Z'
        return fromChar & 0x7f
    match (fromChar):
        case 0xdb:
            return '{'
        case 0xdd:
            return '}'
        case 0xdf:
            return '|'
    if type(fromChar) is str:
        fromChar = int(fromChar)
    return fromChar

def asciiToPetsciiString(fromStr: str) -> str:
    """
    Convert an ASCII string to PETSCII.
    :param fromStr: The ASCII string.
    :return: The string converted to PETSCII.
    """
    toStr: str = ""

    for c in fromStr:
        toStr += chr(asciiToPetsciiChar(ord(c)))
    return toStr

def asciiToPetsciiChar(fromChar: int) -> int:
    """
    Convert a single PETSCII character to ASCII.
    :param fromChar: The character to be converted.
    :return:
    """
    if fromChar < 0x41: # numbers, punctuation, control chars
        if fromChar == 0x0a:
            return 0x0d
        else:
            return fromChar
    if fromChar <= 0x5a: # 'A' - 'Z'
        return fromChar | 0x80
    if fromChar == '\\':
        return 0x5c
    if fromChar < 0x61: # punctuation
        return fromChar
    if fromChar <= 0x7a: # 'a' - 'z'
        return fromChar & 0xdf
    match(fromChar):
        case'_':
            return 0xa4
        case '~':
            return 0xaf
        case '|':
            return 0xdf
        case '{':
            return 0xdb
        case '}':
            return 0xdd
    return fromChar

def getStringWidth(string: str, recordData: bytearray):
    """
    For GEOS, return the width of a string in pixels for a given font.
    :param string: The string to be measured.
    :param recordData: The font data (point-size record).
    :return: The string length in pixels.
    """
    stringWidth = 0

    for char in string:
        stringWidth += getCharWidth(char, recordData)
    return stringWidth

def getMegaStringWidth(string: str, megaFontData: bytearray):
    """
    For GEOS, return the width of a string in pixels for a given mega-font.
    :param string: The string to be measured.
    :param megaFontData: The font data (all seven
    :return:
    """
    stringWidth = 0

    for char in string:
        recordNo = getMegaRecordNo(char)
        stringWidth += getCharWidth(char, megaFontData.get(recordNo))
    return stringWidth

def getCharWidth(char: str, recordData: bytearray):
    """
    Get the width of a character in a GEOS font.
    :param char: The character whose width is to be returned.
    :param recordData: The VLIR record containing font data.
    :return: The width of the character in pixels.
    """
    # subtract bit offset of this character from that of the next
    return getCharacterBitOffset(chr(ord(char) + 1), recordData) \
         - getCharacterBitOffset(char, recordData)

def getMegaRecordNo(char: str):
    """
    For a mega font, get the VLIR record number that the given character
    appears in. Mega fonts store bitstream data in the following records:
    48 pt: $20-$2f (blank to '/')
    49 pt: $30-$3f ('0' to '?')
    50 pt: $40-$4f ('@' to 'O')
    51 pt: $50-$5f ('P' to '_')
    52 pt: $60-$6f ('`' to 'o')
    53 pt: $70-$7f ('p' to DEL)
    :param  c: The character whose record number is to be found.
    :return: The VLIR record number.
    """
    return 46 + (ord(char) >> 4)

def getCharacterBitOffset(char: str, recordData: bytearray):
    """
    Get the offset in bits from the beginning of a bitstream to the bit
    pattern for a given character.
    :param c: The character to find the offset for.
    :param recordData: The VLIR record containing the font.
    :return: The offset of the character from the beginning of a bit stream.
    """
    indexOffset = getFontIndexOffset(recordData)
    # first character is 32, entries are two bytes
    charIndexOffset = indexOffset + ((ord(char) - 32) * 2)
    return makeWord(recordData, charIndexOffset)

def getFontIndexOffset(recordData: bytearray) -> int:
    """
    Get offset to the bistream index table of a font.
    :param recordData: The VLIR record containing the font.
    :return: The index to the bitstream table (generally $0008).
    """
    return makeWord(recordData, FontOffsets.F_INDEX.value)

def getFontDataOffset(recordData: bytearray):
    """
    Get offset to the bitstream data of a font.
    :param  recordData: The VLIR record containing the font.
    :return: The index to the bitstream data (generally $00ca).
    """
    return makeWord(recordData, FontOffsets.F_DATA.value)

def getPointSize(escape: int) -> int:
    """
    Get the point size from a font ID in escape format.
    :param escape: The fontID.
    :return: The point size (lowest six bits).
    """
    return escape & 0x3f

def getFontEscape(fontId: int, pointSize: int) -> int:
    """
    Get the font ID in escape format, given the raw ID and the point size.
    :param fontId: The raw font ID.
    :param pointSize: The point size of the font.
    :return: The font ID in escape format.
    """
    return (fontId << 6) | pointSize

def getFontId(fontSizeId: int) -> int:
    """
    Get the raw font ID from an ID in escape format.
    :param fontSizeId: The font ID.
    :return: The raw font ID (leftmost 10 bits of a two-byte word, shifted).
    """
    return (fontSizeId & 0xffc0) >> 6

def makeWord(data: bytearray, index: int) -> int:
    """
    Helper function: make a word from two little-endian bytes.
    :param data: The data in which the word is found.
    :param index: The location of the first byte.
    :return: The word.
    """
    return data[index] + (data[index + 1] * 256)

#=======================================================================
# return hex dump of passed data
#=======================================================================
def hexDump(data: [], start: int, length: int):
    """
    Generate a traditional hex dump, 16 bytes across.
    :param data: The data to be dumped.
    :param start: The start point within the data for the dump.
    :param length: The length of data to dump.
    :return: A list of strings comprising the dump.
    Usage:
    dump = self.hexDump(data, 0, len(data))
    for line in dump:
        print(line)
    """
    try:
        dump = []
        i = start
        limit = i + length
        while i < limit:
            line = "${0:04x} ".format(i) # address

            # hex dump, 16 characters across
            iSave = i
            for j in range(16):
                if j > 0 and j % 8 == 0:
                    line += " "   # column separator
                if i >= limit:
                    line += "   " # out of data, placeholder
                else:
                    line = line + "{0:02x} ".format(data[i])
                    i += 1
            line += "| "

            i = iSave # now do character representation
            for j in range(16):
                if (j > 0 and j % 8 == 0):
                    line += " "; # column separator
                if i >= limit:
                    line += " "  # out of data, placeholder
                else:
                    c = data[i] & 0xff
                    if c >= 0x20 and c < 0x7f:
                        line += chr(c)
                    else:
                        line += '.'
                    i += 1
            dump.append(line)
    except Exception as exc:
        traceback.format_exc()

    return dump
