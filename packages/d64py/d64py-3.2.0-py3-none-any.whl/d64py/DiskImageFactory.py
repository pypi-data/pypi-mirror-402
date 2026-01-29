#======================================================================
# DiskImageFactory.py
#======================================================================
import logging
import os
from pathlib import Path
from d64py.DiskImage import DiskImage
from d64py import Geometry
from d64py.TrackSector import TrackSector
from d64py.Constants import ImageType
from d64py import D64Utility

def __init__(self):
    super.__init__(self)

def createD64Image(imagePath: Path, diskName: bytearray, id: bytearray) -> DiskImage:
    imageType: ImageType = ImageType.D64
    
    if len(diskName) == 0:
        raise Exception("Disk name cannot be empty.")
    if len(diskName) > 16:
        raise Exception("Disk name must be 16 characters or less.")
    if len(id) != 2:
        raise Exception("Disk ID must be two characters.")
        
    if os.path.exists(imagePath):
        raise Exception("File " + str(imagePath) + " exists!")

    imageName = str(imagePath)
    if len(imageName) < 5 or imageName[len(imageName) - 4] != '.':
        raise Exception("Malformed image name: " + imageName)
    
    with open(imageName, "wb") as imageFile:
        imageFile.truncate(Geometry.imageLength(imageType))
    
        # write empty sectors
        buffer = bytearray(b'\x01') * 256
        buffer[0] = 0
        for track in range(1, Geometry.getMaxTrack(imageType)):
            if track > 1:
                buffer[0] = 0x4b
            for sector in range(Geometry.getMaxSector(imageType, track) + 1):
                imageFile.seek(Geometry.getSectorByteOffset(TrackSector(track, sector), imageType))
                imageFile.write(buffer)
            
        # write directory sectors
        buffer = bytearray(256)
        buffer[0] = 0x12  # next dir track
        buffer[1] = 0x01  # next dir sector
        buffer[2] = 0x41  # DOS type 2A
        buffer[3] = 0x00
        # construct BAM
        for track in range(1, Geometry.getMaxTrack(imageType) + 1):
            # number of free sectors:
            if track == 18: # directory track
                buffer[track * 4] = 17 # header, first dir sector allocated (else 19)
                buffer[(track * 4) + 1] = 0xfc # six sectors free (BAM bits)
            else:
                buffer[track * 4] = Geometry.getMaxSector(imageType, track) + 1
                buffer[(track * 4) + 1] = 0xff # eight sectors free (BAM bits)
            buffer[(track * 4) + 2] = 0xff # eight sectors free (BAM bits)
            zone = Geometry.getZone(imageType, track)
            match zone:
                case 0: # tracks 1-17
                    buffer[(track * 4) + 3] = 0x1f # five more sectors
                case 1: # tracks 18-24
                    buffer[(track * 4) + 3] = 0x07 # three more sectors
                case 2: # tracks 25-30
                    buffer[(track * 4) + 3] = 0x03 # two more sectors
                case 3: # tracks 31-35
                    buffer[(track * 4) + 3] = 0x01 # one more sector

        i = 0
        while i < len(diskName):
            buffer[Geometry.getDiskNameOffset(imageType) + i] = ord(diskName[i])
            i += 1
        while i < 18: # also two 0xa0 between name and ID
            buffer[Geometry.getDiskNameOffset(imageType) + i] = 0xa0
            i += 1
        i += Geometry.getDiskNameOffset(imageType)
        buffer[i] = ord(id[0]); i += 1
        buffer[i] = ord(id[1]); i += 1
        buffer[i] = 0xa0; i += 1
        buffer[i] = 0x32; i += 1 # DOS type
        buffer[i] = 0x41; i += 1
        j = 0
        while j < 4: # four more 0xa0
            buffer[i] = 0xa0
            i += 1
            j += 1
        while i < 256:
            buffer[i] = 0
            i += 1

        imageFile.seek(Geometry.getSectorByteOffset(
                       Geometry.getDirHeaderTrackSector(imageType), imageType))
        imageFile.write(buffer)
        
        # write first directory sector
        buffer = bytearray(256)
        buffer[1] = 0xff
        imageFile.seek(Geometry.getSectorByteOffset(
                       Geometry.getFirstDirTrackSector(imageType), imageType))
        imageFile.write(buffer)
    imageFile.close()
    return DiskImage(imagePath)
   
#-----------------------------------------------------------------------
   
def createD81Image(imagePath: Path, diskName: bytearray, id: bytearray) -> DiskImage:
    imageType: ImageType = ImageType.D81
    
    if len(diskName) == 0:
        raise Exception("Disk name cannot be empty.")
    if len(diskName) > 16:
        raise Exception("Disk name must be 16 characters or less.")
    if len(id) != 2:
        raise Exception("Disk ID must be two characters.")
        
    if os.path.exists(imagePath):
        raise Exception("File " + str(imagePath) + " exists!")

    imageName = str(imagePath)
    if len(imageName) < 5 or imageName[len(imageName) - 4] != '.':
        raise Exception("Malformed image name: " + imageName)
    
    with open(imageName, "wb") as imageFile:
        imageFile.truncate(Geometry.imageLength(imageType))
        
        # write empty sectors
        buffer = bytearray(256)
        for track in range(1, Geometry.getMaxTrack(imageType) + 1):
            sector = 0
            while sector < Geometry.getMaxSector(imageType, track):
                imageFile.seek(Geometry.getSectorByteOffset(
                                TrackSector(track, sector), imageType))
                imageFile.write(buffer)
                sector += 1
            
        # write directory header
        buffer[0] = 0x28 # next dir track
        buffer[1] = 0x03 # next dir sector
        buffer[2] = 0x44 # DOS type
        buffer[3] = 0x00
        i = 0
        
        while i < len(diskName):
            buffer[Geometry.getDiskNameOffset(imageType) + i] = ord(diskName[i])
            i += 1
        while i < 18: # also two 0xa0 between name and ID
            buffer[Geometry.getDiskNameOffset(imageType) + i] = 0xa0
            i += 1
        i += Geometry.getDiskNameOffset(imageType)
        buffer[i] = ord(id[0]); i += 1
        buffer[i] = ord(id[1]); i += 1
        buffer[i] = 0xa0; i += 1
        buffer[i] = 0x33; i += 1 # DOS version
        buffer[i] = 0x44; i += 1
        buffer[i] = 0xa0; i += 1 # two more 0xa0
        buffer[i] = 0xa0; i += 1 # two more 0xa0
        while i < 256:
            buffer[i] = 0; i += 1
        ts = Geometry.getDirHeaderTrackSector(imageType)
        imageFile.seek(Geometry.getSectorByteOffset(ts, imageType))
        imageFile.write(buffer)
        
        # write BAM sector 1:
        buffer = bytearray(256)
        buffer[0] = 0x38 # next dir track
        buffer[1] = 0x02 # next dir sector
        buffer[2] = 0x44 # DOS version
        buffer[3] = 0xbb # DOS version complement
        buffer[4] = ord(id[0])
        buffer[5] = ord(id[1])
        buffer[6] = 0xc0 # I/O byte
        buffer[7] = 0 # auto-loader flag
        for i in range(8, 16):
            buffer[i] = 0
            
        for track in range(1, 40):
            offset = ((track - 1) * 6) + 16
            buffer[offset] = 0x28 # free sectors
            for j in range(1, 6):
                buffer[offset + j] = 0xff # eight sectors free (BAM)
        offset = (39 * 6) + 16 # BAM track 40 (directory track)
        buffer[offset] = 0x24 # free sectors
        buffer[offset + 1] = 0xf0 # first four sectors used
        for j in range(2, 6):
            buffer[offset + j] = 0xff # eight sectors free (BAM)
        ts.sector = ts.sector + 1
        imageFile.seek(Geometry.getSectorByteOffset(ts, imageType))
        imageFile.write(buffer)

        # write BAM sector 2:
        buffer = bytearray(256)
        buffer[0] = 0x00 # next dir track
        buffer[1] = 0xff # next dir sector
        buffer[2] = 0x44 # DOS version
        buffer[3] = 0xbb # DOS version complement
        buffer[4] = ord(id[0])
        buffer[5] = ord(id[1])
        buffer[6] = 0xc0 # I/O byte
        buffer[7] = 0    # auto-loader flag
        for i in range(8, 16):
            buffer[i] = 0
        for track in range(41, 81):
            offset = ((track - 41) * 6) + 16
            buffer[offset] = 0x28 # free sectors
            j = 1
            while j <= 5:
                buffer[offset + j] = 0xff # eight sectors free (BAM)
                j += 1
        ts.sector = ts.sector + 1
        imageFile.seek(Geometry.getSectorByteOffset(ts, imageType))
        imageFile.write(buffer)
            
        # write first directory sector
        buffer = bytearray(256)
        buffer[1] = 0xff
        imageFile.seek(Geometry.getSectorByteOffset(
                       Geometry.getFirstDirTrackSector(imageType), imageType))
        imageFile.write(buffer)
        imageFile.close()
        
    return DiskImage(imagePath)
