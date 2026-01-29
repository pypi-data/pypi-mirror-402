#======================================================================
# DirHeader.py
#======================================================================
from d64py.Constants import ImageType
from d64py import Geometry

class DirHeader:
    def __init__(self, raw: bytearray, imageType: ImageType):
        self.raw = raw
        unRaw = bytearray(16)
        self.imageType = imageType
        diskNameOffset = Geometry.getDiskNameOffset(self.imageType)

        for i in range(16):
            unRaw[i] = raw[i + diskNameOffset] & 0x7f
        self.diskName = unRaw.decode("ascii")
        # same for D64 and D81:
        self.diskId = self.raw[diskNameOffset + 18 : diskNameOffset + 20]
        if self.isGeosDisk():
            self.geosIdString = raw[173:189].decode("ascii")
            self.geosMasterDisk = (raw[189] == "P")
        else:
            self.geosIdString = ""
            self.geosMasterDisk = False

    def getDiskId(self):
        return self.diskId

    def getDiskName(self):
        return self.diskName

    def getGeosIdString(self):
        return self.geosIdString

    def getRaw(self):
        return self.raw

    def getRawDiskName(self):
        return self.raw[Geometry.getDiskNameOffset(self.imageType), \
                        Geometry.getDiskNameOffset(self.imageType + 16)]

    def isGeosDisk(self) -> bool:
        return self.raw[173:177] == "GEOS"

    def isGeosMasterDisk(self):
        return self.geosMasterDisk

    
