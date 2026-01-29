#======================================================================
# Geometry.py
#======================================================================
from d64py.Constants import ImageType
from d64py.TrackSector import TrackSector

def imageLength(imageType: ImageType) -> int:
    """
    Get the expected length for an image type.
    :param imageType: The type of disk image.
    :return: The expected length.
    """
    if not isinstance(imageType, ImageType):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64:
            return 174848
        case ImageType.D64_ERROR:
            return 175531
        case ImageType.D81:
            return 819200

def getErrorOffset(imageType: ImageType) -> int:
    """
    Get the offset to the image's error table.
    Only valid for images of type D64_ERROR.
    :param imageType: The image type.
    :return: The offset to the error table.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64_ERROR:
            return 174848
        case _:
            raise Exception("Not an error image.")

def getSectorSize(imageType: ImageType) -> int:
    """
    Get the sector size for an image type.
    :param imageType: The image type.
    :return: The sector size.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")
    return 256; #all types have 256-byte sectors

def isValidTrackSector(ts: TrackSector, imageType: ImageType) -> bool:
    """
    Test whether a track and sector is valid for the image type.
    :param ts: A TrackSector object.
    :param imageType: The image type.
    :return: True if the TrackSector is valid, False otherwise.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    if (ts.track < 1 or ts.track > getMaxTrack(imageType)):
        return False
    else:
        if (ts.sector < 0 or ts.sector > getMaxSector(imageType, ts.track)):
            return False
        else:
            return True

def getMaxTrack(imageType: ImageType) -> int:
    """
    Get the highest track number for an image type.
    :param imageType: The image type.
    :return: The highest track number.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 35
        case ImageType.D81:
            return 80

def getMaxSector(imageType: ImageType, track: int) -> int:
    """
    Get the highest sector number for a track in the given image type.
    :param imageType: The image type.
    :param track: The track.
    :return: The highest sector number.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            zone = getZone(imageType, track)
            match zone:
                case 0:
                    return 20
                case 1:
                    return 18
                case 2:
                    return 17
                case 3:
                    return 16
        case ImageType.D81:
            return 39

def getZone(imageType: ImageType, track: int) -> int:
    """
    For D64 images, get the density zone in which a track appears.
    :param imageType: The image type (only D64 and D64_ERROR are valid).
    :param track: The track.
    :return: The zone in which the track appears (0-3).
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            if (track <= 17):
                return 0
            elif (track <= 24):
                return 1
            elif (track <= 30):
                return 2
            elif (track <= 35):
                return 3
        case _:
            raise Exception(f"A {imageType.description} does not have zones.")

def getDirectoryTrack(imageType: ImageType) -> int:
    """
    For a given image type, get the track in which the directory is stored.
    :param imageType: The image type.
    :return: The track containing the directory.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 18
        case ImageType.D81:
            return 40

def getDirHeaderTrackSector(imageType: ImageType) -> TrackSector:
    """
    For a given image type, get the track and sector of the directory header.
    :param imageType: The image type.
    :return: A TrackSector object.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return TrackSector(18, 0)
        case ImageType.D81:
            return TrackSector(40, 0)

def getDiskNameOffset(imageType: ImageType) ->  int:
    """
    For a given image type, get the offset to the disk name
    in the directory header.
    :param imageType: The image type.
    :return: The offset to the disk name.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 144
        case ImageType.D81:
            return 4

def getFirstDirTrackSector(imageType: ImageType) -> TrackSector:
    """
    For a given image type, get the track and sector where the
    directory starts.
    :param imageType: The image type.
    :return: A TrackSector object.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return TrackSector(18, 1)
        case ImageType.D81:
            return TrackSector(40, 3)

def getMaxBlocksFree(imageType: ImageType) -> int:
    """
    Get the maximum number of free blocks for an image type.
    :param imageType: The image type.
    :return: The number of free blocks.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 664
        case ImageType.D81:
            return 3160

def getSectorOffset(ts: TrackSector, imageType: ImageType) -> int:
    """
    Given a track and sector, return the sector offset into the image
    (i.e. the total number of sectors from the start of the image).
    :param ts: A TrackSector object.
    :param imageType: The image's type.
    :return: The byte offset of the track and sector.
    """
    sectorOffset: int = 0

    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            if ts.track > 17:
                sectorOffset += 17 * 21
                if ts.track > 24:
                    sectorOffset += 7 * 19
                    if ts.track > 30: #tracks 31-35
                        sectorOffset += 6 * 18
                        sectorOffset += (ts.track - 31) * 17
                    else: #tracks 25-30
                        sectorOffset += (ts.track - 25) * 18
                else: #tracks 18-24
                    sectorOffset += (ts.track - 18) * 19
            else: #tracks 1-17
                sectorOffset += (ts.track - 1) * 21
            sectorOffset += ts.sector

        case ImageType.D81:
            sectorOffset += (ts.track - 1) * 40
            sectorOffset += ts.sector

    return sectorOffset

def getOffsetSector(offset: int, imageType: ImageType) -> TrackSector:
    """
    Given a byte offset into an image, return the track and sector.
    :param offset: The offset in bytes.
    :param imageType: The image's type.
    :return: A TrackSector object.
    """
    track = 0; sector = 0; zoneOffset = 0

    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            #zone 1 (tracks 1-17)
            if offset <= 17 * 21: #tracks 1-17 * no. sectors in zone
                track = (offset // 21) + 1
                sector = offset % 21
                return TrackSector(track, sector)
            zoneOffset = offset - (17 * 21)

            #zone 2 (tracks 18-24)
            if zoneOffset <= 7 * 19:
                track = 18 + (zoneOffset // 19) #tracks 18-24 * no. sectors in zone
                sector = zoneOffset % 19
                return TrackSector(track, sector)
            zoneOffset -= 7 * 19

            #zone 3 (tracks 25-30)
            if zoneOffset <= 6 * 18: #tracks 25-30 * no. sectors in zone
                track = 25 + (zoneOffset // 18)
                sector = zoneOffset % 18
                return TrackSector(track, sector)
            zoneOffset -= 6 * 18

            #zone 4 (tracks 31-35)
            if zoneOffset <=5 * 17: #tracks 31-35 * no. sectors in zone
                track = 31 + (zoneOffset // 17)
                sector = zoneOffset % 17
                return TrackSector(track, sector)

        case ImageType.D81:
            track = (offset // 40) + 1
            sector = offset % 40

    return TrackSector(track, sector)

def getSectorByteOffset(ts: TrackSector, imageType: ImageType) -> int:
    """
    For a given image type, get the offset in bytes to a track and sector.
    :param ts: A TrackSector object.
    :param imageType: The image type.
    :return: The byte offset.
    """
    if not isValidTrackSector(ts, imageType):
        raise Exception(f"Invalid track and sector: {ts}")
    return getSectorOffset(ts, imageType) * getSectorSize(imageType)

def getBamSize(imageType: ImageType) -> int:
    """
    For a given image type, return the number of bytes in the
    Block Availability Map.
    :param imageType: The image type.
    :return: The size of the BAM.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 140
        case ImageType.D81:
            return 480

def getBamBytesPerTrack(imageType: ImageType) -> int:
    """
    For a given image type, return the number of bytes used
    to store the block availability map for a single track.
    :param imageType:
    :return: The number of bytes.
    """
    if not (isinstance(imageType, ImageType)):
        raise Exception("Must pass an image type.")

    match imageType:
        case ImageType.D64 | ImageType.D64_ERROR:
            return 4
        case ImageType.D81:
            return 6

