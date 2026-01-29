#======================================================================
# Chain.py
#======================================================================
import logging
import d64py.TrackSector as TrackSector

class Chain:
    sectors: list[TrackSector]

    def __init__(self, sectors):
        if sectors is None:
            self.sectors = []
        self.sectors = sectors

    def add(self, ts):
        self.sectors.append(ts)

    def size(self) -> int:
        return len(self.sectors)

    def contains(self, ts) -> bool:
        for sector in sectors:
          thisTs = sector
          if thisTs == ts:
            return True
        return False

    def  __str__(self):
        chains = ""
        for ts in self.sectors:
            chains += str(ts) + " "
        return chains