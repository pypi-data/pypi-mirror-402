### This project is a Python library for writing programs to explore Commodore 64 disk images; my Disk Wrangler (q.v.) is based on it. It's particularly good at dissecting GEOS disks. Here's how to get started:

**Create a DiskImage object. Just pass a Path to the constructor; he'll detect the image type (or raise an Exception if it's not one):**

```
from pathlib import Path
from d64py.DiskImage import DiskImage
from d64py.Constants import CharSet

path = Path("/your/image/here.d64")
image = DiskImage(path)
```

**Now you can read the directory:**

```
dirEntries = image.getDirectory()
for dirEntry in dirEntries:
    print(f"{dirEntry.getDisplayFileName()}")
```

**If you have a GEOS file, you can access the fields in the file header:**

```
    if dirEntry.isGeosFile():
        geosFileHeader = dirEntry.getGeosFileHeader()
        print(f"permanent name string: {geosFileHeader.getPermanentNameString()}")
```

**Say there's a geoWrite file on the disk, and you'd like to quickly see what's in it. We can ask the disk image to find the directory entry for us (if we specify CharSet.PETSCII, the filename will be translated to PETSCII first). All the routines that return lines of text return TextLine objects, which is just a helper class that includes a line of text and an error flag (for e.g. printing in red). geoWrite files return a list of pages, each of which is a list of TextLines.**

```
dirEntry = image.findDirEntry("firstBootSrc", CharSet.ASCII)
pages = image.getGeoWriteFileAsLines(dirEntry)
for page in pages:
    for line in page:
        print(line.text)
```

**Don't forget to release the image's resources when you're through with it (the entire image gets memory-mapped):**

```
image.close()
```

