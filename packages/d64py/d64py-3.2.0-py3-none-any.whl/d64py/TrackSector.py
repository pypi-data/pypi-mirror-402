#======================================================================
# TrackSector.py
#======================================================================
class TrackSector:
    def __init__(self, track: int, sector: int):
        self.track = track
        self.sector = sector

    def __eq__(self, other):
        if not isinstance(other, TrackSector):
            raise Exception(f"Can't compare {type(other)} to TrackSector!")
        return (self.track == other.track and self.sector == other.sector)

    def __str__(self):
        return f'{self.track:02d}' + '/' + f'{self.sector:02d}'

    def __hash__(self):
        hash = 3
        hash = 17 * hash + self.track
        hash = 17 * hash + self.sector
        return hash

    def isEof(self):
        return (self.track == 0)

