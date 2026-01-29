#======================================================================
# D64Gfx.py
#======================================================================
from enum import Enum, auto
import logging
from PyQt6.QtCore import QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMessageBox
from d64py.Constants import *
from d64py import DirEntry, DiskImage
from d64py import D64Utility
from d64py.Exceptions import InvalidRecordException

class ImageParams(Enum):
    DATA_SIZE = 1280 # 80 cards wide X 2 card rows per record
    COLOR_SIZE = 160
    BUFFER_SIZE = DATA_SIZE + 8 + COLOR_SIZE # pixels, null card, colors

class CorruptType(Enum):
    MISSING_DATA = auto()
    EXTRA_DATA   = auto()
    NULL_BYTE    = auto()

class Palettes:
    def __init__(self):
        # "Pepto" colors (https://www.pepto.de/projects/colorvic/2001/):
        self.peptoColors = [ 
            0xFF000000, # black
            0xFFFFFFFF, # white
            0xFF68372B, # red
            0xFF70A4B2, # cyan
            0xFF6F3D86, # purple
            0xFF588D43, # green
            0xFF352879, # blue
            0xFFB8C76F, # yellow
            0xFF6F4F25, # orange
            0xFF433900, # brown
            0xFF9A6759, # light red
            0xFF444444, # dark grey
            0xFF6C6C6C, # medium grey
            0xFF9AD284, # light green
            0xFF6C5EB5, # light blue
            0xFF959595  # light grey
        ]            

        self.peptoNtscSonyColors = [
            0xFF000000,
            0xFFFFFFFF,
            0xFF7C352B,
            0xFF5AA6B1,
            0xFF694185,
            0xFF5D8643,
            0xFF212E78,
            0xFFCFBE6F,
            0xFF894A26,
            0xFF5B3300,
            0xFFAF6459,
            0xFF434343,
            0xFF6B6B6B,
            0xFFA0CB84,
            0xFF5665B3,
            0xFF959595
        ]    

        self.colodoreColors = [
            0xFF000000,
            0xFFFFFFFF,
            0xFF813338,
            0xFF75CEC8,
            0xFF8D3C97, 
            0xFF56AC4D, 
            0xFF2E2C9A, 
            0xFFEDF172, 
            0xFF8D502A, 
            0xFF553800,
            0xFFC46C71,
            0xFF4A4A4A, 
            0xFF7B7B7B, 
            0xFFAAFFA0,
            0xFF706DEB, 
            0xFFB2B2B2
        ]

class Palette(Enum):
    PEPTO = auto()
    PEPTO_NTSC_SONY = auto()
    COLODORE = auto()

def getGeosIcon(dirEntry: DirEntry):
    """
    Given a directory entry, get the icon for a GEOS file from its file
    header as a Qt6 QImage.
    :param dirEntry: The directory entry.
    :return: The icon.
    """
    try:
        geosFileHeader = dirEntry.getGeosFileHeader()
        if not geosFileHeader:
            raise Exception(f"{dirEntry.getDisplayFileName()}: can't read GEOS file header")
    except Exception as exc:
        raise

    iconData = geosFileHeader.getIconData()
    rawImage = QImage(QSize(24, 21), QImage.Format.Format_Mono)
    rawImage.fill(0)  # clear it
    index = 0
    while index < len(iconData):
        y = index // 3
        card = index % 3  # icon is three bytes across
        bit = 0
        while bit < 8:
            mask = (1 << bit)
            data = 0 if iconData[index] & mask else 1
            x = (7 - bit) + (card * 8)
            rawImage.setPixel(QPoint(x, y), data)
            bit += 1
        index += 1
    rawImage = rawImage.scaled(QSize(48, 42)) #double size
    return rawImage

def getFontPreviewImage(text: str, recordData: bytearray) -> QImage:
    """
    Generate a preview image of a normal GEOS font as a Qt6 QImage.
    :param text: The text to render.
    :param recordData: The VLIR record containing the font data.
    :return: A QImage.
    """
    textWidth = D64Utility.getStringWidth(text, recordData)
    height = recordData[FontOffsets.F_HEIGHT.value]
    rawImage = QImage(QSize(textWidth, height), QImage.Format.Format_Mono)
    setWidth = D64Utility.makeWord(recordData, FontOffsets.F_SETWD.value)
    row = 0
    while (row < height):
        rasterX = 0 # X pixel position of image
        for char in text:
            width = D64Utility.getCharWidth(char, recordData)
            bitIndex = D64Utility.getCharacterBitOffset(char, recordData)
            byteIndex = bitIndex // 8
            byteIndex += D64Utility.getFontDataOffset(recordData)
            byteIndex += setWidth * row
            bitOffset = bitIndex % 8
            bitsCopied = 0

            while bitsCopied < width:
                if byteIndex >= len(recordData):
                    # Shouldn't happen but I've seen fonts (AGATHA) where it does.
                    logging.debug(f"*** NOT ENOUGH DATA: byte index: {byteIndex}, record length: {len(recordData)}")
                    byte = 0
                else:
                    byte = recordData[byteIndex]
                fontBits = min(8 - bitOffset, width - bitsCopied)
                i = bitOffset
                while i < bitOffset + fontBits:
                    mask = 1 << 7 - i
                    rawImage.setPixel(QPoint(rasterX, row), 0 if byte & mask else 1)
                    rasterX += 1
                    i += 1
                bitsCopied += fontBits
                bitOffset = 0 # for bytes after the first one
                byteIndex += 1
        row += 1
    rawImage = rawImage.scaled(QSize(textWidth * 2, height * 2))
    return rawImage

def getMegaFontPreviewImage(text: str, megaFontData: bytearray) -> QImage:
    """
    Generate a preview image of a GEOS mega font as a Qt6 QImage.
    :param text: The text to render.
    :param recordData: The font data from all the mega font records.
    :return: A QImage.
    """
    height = megaFontData.get(54)[FontOffsets.F_HEIGHT.value]
    textWidth = D64Utility.getMegaStringWidth(text, megaFontData)
    rawImage = QImage(QSize(textWidth, height), QImage.Format.Format_Mono)
    row = 0
    while row < height:
        rasterX = 0
        for char in text:
            recordNo = D64Utility.getMegaRecordNo(char)
            recordData = megaFontData.get(recordNo)
            setWidth = D64Utility.makeWord(recordData, FontOffsets.F_SETWD.value)
            width = D64Utility.getCharWidth(char, recordData)
            bitIndex = D64Utility.getCharacterBitOffset(char, recordData)
            byteIndex = bitIndex // 8
            byteIndex += D64Utility.getFontDataOffset(recordData)
            byteIndex += setWidth * row
            bitOffset= bitIndex % 8
            bitsCopied = 0

            while bitsCopied < width:
                if byteIndex >= len(recordData):
                    # Shouldn't happen, but I've seen fonts
                    # (MEGA BRUSHSTROKE) where it does.
                    byte = 0
                else:
                    byte = recordData[byteIndex]
                fontBits = min(8 - bitOffset, width - bitsCopied)
                i = bitOffset
                while i < bitOffset + fontBits:
                    mask = 1 << (7 - i)
                    rawImage.setPixel(QPoint(rasterX, row), 0 if byte & mask else 1)
                    i += 1; rasterX += 1
                bitsCopied += fontBits
                bitOffset= 0 # for bytes after the first one
                byteIndex += 1
        row += 1
    rawImage = rawImage.scaled(QSize(textWidth * 2, height * 2))
    return rawImage

class ImagePreviewer:
    '''
    Previewer for geoPaint files and photo scraps/photo albums.
    '''
    def __init__(self, palette):
        palettes = Palettes()
        match palette:
            case Palette.PEPTO:
                self.screenColors = palettes.peptoColors
            case Palette.PEPTO_NTSC_SONY:
                self.screenColors = palettes.peptoNtscSonyColors
            case Palette.COLODORE:
                self.screenColors = palettes.colodoreColors

    def getPhotoAlbumPreviews(self, dirEntry: DirEntry, diskImage: DiskImage):
        """
        Get previews of the scraps in a photo album.
        :param dirEntry: The directory entry of the photo album to view.
        :param diskImage: The disk image of the file.
        :return: A list of PhotoScrap objects including the QPixmaps.
        """
        index = diskImage.getGeosVlirIndex(dirEntry)
        version = dirEntry.getGeosFileHeader().getPermanentNameVersion()
        logging.info(f"photo album {dirEntry.getDisplayFileName()} is version {version}")
        if version == "V2.1": # supports named scraps
            record = 0; namesRecordNo = -1
            while record < 127: # find last record (contains names)
                offset = (record + 1) * 2  # convert VLIR record no. to sector index
                if not index[offset]:
                    if record > 0:
                        namesRecordNo = record - 1 
                        logging.debug(f"found names record at {namesRecordNo}")
                        namesRecord = diskImage.readVlirRecord(namesRecordNo, dirEntry)
                        break
                record += 1
                
        photoScraps = []
        record = 0; scraps = 0
        while record < 127:
            offset = (record + 1) * 2  # convert VLIR record no. to sector index
            if index[offset]: # non-empty record
                data = diskImage.readVlirRecord(record, dirEntry) # read photo scrap
                if len(data) == 0: # probably a corrupt disk image
                    record += 1
                    continue
                if version == "V2.1" and record == namesRecordNo:
                    record += 1
                    continue
                width = data[0] # width in bytes
                height = data[1] + (data[2] * 256) # height in scanlines
                self.rawImage = QImage(QSize(width * 8, height), QImage.Format.Format_Indexed8)
                
                i = 0
                while i < 16: # set up color table
                    self.rawImage.setColor(i, self.screenColors[i])
                    i += 1
                    
                if version == "V2.1":
                    try :
                        if len(namesRecord) == 0: #probably a corrupt disk image
                            name = f"Photo #{record + 1}"
                        elif namesRecord[0] < 0x20: # same
                            name = f"Photo #{record + 1}"
                        else:
                            slicePoint = 1 + (record * 17); i = 0 # one for scrap count
                            while namesRecord[slicePoint + i]: # stop at the null
                                i += 1
                            nameBytes = namesRecord[slicePoint : (slicePoint + i)]
                            name = nameBytes.decode() # it's already ASCII
                    except Exception as exc:
                        logging.debug("Corrupt names record!")
                        name = f"Photo #{record + 1}"
                else:
                    name = f"Photo #{record + 1}"
                    
                numDataBytes = (int)(width * height)
                numColorBytes = (int)(numDataBytes / 8)
                self.decompressedBytes = [0] * (numDataBytes + numColorBytes)
                self.inputIndex = 3 # past width/height
                
                # -------------------------------------------------
                # Decompress data and plot pixels with color data.
                # -------------------------------------------------
                try:
                    decompressed = self.decompressPhotoAlbumRecord(data, self.decompressedBytes, numDataBytes + numColorBytes, name)
                except Exception as exc:
                    raise exc
                if not decompressed:
                    record += 1
                    continue

                colorBase = width * height # location of color table
                self.outIndex = 0; scanline = 0
                while scanline < height:
                    i = 0
                    while i < width:
                        pixelData = self.decompressedBytes[self.outIndex]
                        colorIndex = (int(scanline / 8) * int(width)) + i
                        try:
                            colors = self.decompressedBytes[colorBase + colorIndex]
                        except Exception as exc:
                            raise exc
                        fg = (colors & 0xf0) >> 4
                        bg = colors & 0x0f

                        j = 0
                        while j < 8:
                            mask = (1 << (7 - j))
                            data = fg if pixelData & mask else bg
                            x = (i * 8) + j
                            y = scanline
                            self.rawImage.setPixel(QPoint(x,y),data)
                            j += 1
                        i += 1
                        self.outIndex += 1
                    scanline += 1
                    
                self.rawImage = self.rawImage.scaled(QSize((width * 8) * 2, height * 2))
                photoScrap = PhotoScrap(width, height, QPixmap.fromImage(self.rawImage), name)
                photoScraps.append(photoScrap)
                scraps += 1
            else:
                break # no non-empty records in photo albums
            record += 1
        return photoScraps

    def getPhotoScrapPreview(self, dirEntry: DirEntry, diskImage: DiskImage):
        """
        Get preview of a single photo scrap.
        :param dirEntry: The directory entry of the photo scrap.
        :return: The preview as a PhotoScrap object (including a QPixmap).
        """
        photoScraps = []
        ts = dirEntry.getFileTrackSector()
        data = diskImage.readChain(ts)
        width = data[0] # width in bytes
        height = data[1] + (data[2] * 256) # height in scanlines
        self.rawImage = QImage(QSize(width * 8, height), QImage.Format.Format_Indexed8)
        
        i = 0
        while i < 16: # set up color table
            self.rawImage.setColor(i, self.screenColors[i])
            i += 1
        
        numDataBytes = (int)(width * height)
        numColorBytes = (int)(numDataBytes / 8)
        self.decompressedBytes = [0] * (numDataBytes + numColorBytes)
        self.inputIndex = 3 # past width/height
        
        # Decompress data and plot pixels with color data.
        try:
            # "This photo scrap" is for an error message
            decompressed = self.decompressPhotoAlbumRecord(data, self.decompressedBytes, numDataBytes + numColorBytes, "This photo scrap")
        except Exception as exc:
            raise exc
        
        colorBase = width * height # location of color table
        self.outIndex = 0; scanline = 0
        while scanline < height:
            i = 0
            while i < width:
                pixelData = self.decompressedBytes[self.outIndex]
                colorIndex = (int(scanline / 8) * int(width)) + i
                try:
                    colors = self.decompressedBytes[colorBase + colorIndex]
                except Exception as exc:
                    raise exc
                fg = (colors & 0xf0) >> 4
                bg = colors & 0x0f

                j = 0
                while j < 8:
                    mask = (1 << (7 - j))
                    data = fg if pixelData & mask else bg
                    x = (i * 8) + j
                    y = scanline
                    self.rawImage.setPixel(QPoint(x,y),data)
                    j += 1
                i += 1
                self.outIndex += 1
            scanline += 1
            
        self.rawImage = self.rawImage.scaled(QSize((width * 8) * 2, height * 2))
        photoScrap = PhotoScrap(width, height, QPixmap.fromImage(self.rawImage), "Photo Scrap")
        photoScraps.append(photoScrap)
        return photoScraps

    def decompressPhotoAlbumRecord(self, inBuffer: bytearray, outBuffer: bytearray, bitmapSize: int, name: str) -> bool:
        """
        Decompress a single photo scrap to the combined pixel and color buffer.
        :param inBuffer: The bytes to decompress (uses self.inputIndex).
        :param outBuffer: Buffer for decompressed data.
        :param bitmapSize: Size of bitmap (without color data).
        """
        outIndex = 0; bytesDecompressed = 0
        while bytesDecompressed < bitmapSize:
            if self.inputIndex >= len(inBuffer):
                logging.debug(f"Missing data, index: {self.inputIndex}, buffer size: {len(inBuffer)}")
                QMessageBox.warning(None, "Warning", f"{name} is corrupt (missing data).", QMessageBox.StandardButton.Ok)
                return False
            cmd = inBuffer[self.inputIndex]
            self.inputIndex += 1  # point to data
            if not cmd:
                logging.debug(f"null command byte at {self.inputIndex}")
                QMessageBox.warning(None, "Warning", f"{name} is corrupt (null compression byte).", QMessageBox.StandardButton.Ok)
                return False
                
            if cmd < 128: # repeat next byte "count" times
                count = cmd
                # logging.debug(f'cmd at {"${0:02x}".format(self.inputIndex)} is {"${0:02x}".format(cmd)}, repeat next byte {count} times')
                j = 0
                while j < count:
                    if self.inputIndex >= len(inBuffer):
                        logging.debug(f"Missing data: index is {self.inputIndex}, buffer size is {len(inBuffer)}")
                        QMessageBox.warning(None, "Warning", f"{name} is corrupt (missing data).", QMessageBox.StandardButton.Ok)
                        return False
                    outBuffer[outIndex] = inBuffer[self.inputIndex]
                    outIndex += 1
                    j += 1
                bytesDecompressed += count
                self.inputIndex += 1  # point to next command

            elif cmd < 221: # next "count" bytes are data
                count = cmd - 128
                # logging.debug(f'cmd at {"${0:02x}".format(self.inputIndex)} is {"${0:02x}".format(cmd)}, next {count} bytes are data')
                j = 0
                while j < count:
                    if self.inputIndex + j >= len(inBuffer):
                        logging.error(f"extra data (input index {self.inputIndex + j}, buffer length {len(inBuffer)})")
                        QMessageBox.warning(None, "Warning", f"{name} is corrupt (extra data).", QMessageBox.StandardButton.Ok)
                        return False
                    outBuffer[outIndex] = inBuffer[self.inputIndex + j]
                    outIndex += 1
                    j += 1
                bytesDecompressed += count
                self.inputIndex += count  # point to next command

            else: # next byte is BIGCOUNT, repeat following count-220 bytes BIGCOUNT times
                count = cmd - 220
                self.inputIndex += 1
                bigCount = inBuffer[self.inputIndex]
                self.inputIndex += 1
                # logging.debug(f'cmd at {"${0:02x}".format(self.inputIndex)} is {"${0:02x}".format(cmd)}, next byte is BIGCOUNT: repeat following count-220 ({count - 220}) bytes {bigCount} times')
                i = 0 # BIGCOUNT
                while i < bigCount:
                    j = 0 # count
                    while j < count:
                        outBuffer[outIndex] = inBuffer[self.inputIndex + j]
                        outIndex += 1
                        if outIndex == len(outBuffer):
                            logging.error(f"extra data (input index {self.inputIndex + j}, buffer length {len(inBuffer)})")
                            QMessageBox.warning(None, "Warning", f"{name} is corrupt (extra data).", QMessageBox.StandardButton.Ok)
                            return False
                        j += 1
                self.inputIndex += (count * bigCount)
                bytesDecompressed += (counnt * bigCount)
        return True
        
    def getGeoPaintPreview(self, dirEntry: DirEntry, diskImage : DiskImage):
        """
        Get a preview image of a geoPaint file.
        :param dirEntry: The directory entry of the geoPaint file to view.
        :param diskImage: The disk image of the file.
        :return: A QPixmap that can be attached to a QLabel.
        """
        self.errors = set()

        #--------------------------------------------
        # Get height of image (width is always 640).
        #--------------------------------------------
        index = diskImage.getGeosVlirIndex(dirEntry)
        record = 0; records = 0
        # geoPaint files have 45 records (0-44) of two card rows each,
        # or fewer if the image is shorter (width is always the same)
        while record < 45:
            offset = (record + 1) * 2  # convert VLIR record no. to sector index
            if index[offset]: # non-empty record
                records += 1
            record += 1
        goodRecords = records
        logging.debug(f"start: records: {records}, good: {goodRecords}")
        height = records * 16 # two card rows per record
        logging.info(f"{records} non-empty records found, image will be {height} pixels tall")

        if records < 45:
            self.rawImage = QImage(QSize(640, 16 * records), QImage.Format.Format_Indexed8)
        else:
            self.rawImage = QImage(QSize(640, 720), QImage.Format.Format_Indexed8)
        i = 0
        while i < 16: # set up color table
            self.rawImage.setColor(i, self.screenColors[i])
            i += 1

        # -------------------------------------------------
        # Decompress data and plot pixels with color data.
        # -------------------------------------------------
        self.card = 0; self.row = 0  # coordinates into image
        self.cardRow = 0  # two card rows per VLIR record
        record = 0

        while record < 45:
            self.decompressedBytes = [0] * ImageParams.BUFFER_SIZE.value
            if not index[(record +1) * 2]: # ignore deleted records
                record += 1
                continue

            try:
                self.vlirBuffer = diskImage.readVlirRecord(record, dirEntry)
            except InvalidRecordException as exc:
                logging.exception(exc)
                record += 1
                goodRecords -= 1
                logging.debug(f"decrement 2, {goodRecords}/{records}")
                continue

            # decompress pixel and color data
            self.inputIndex = 0
            try:
                self.decompressGeoPaintRecord(self.vlirBuffer, self.decompressedBytes, ImageParams.BUFFER_SIZE.value)
            except Exception as exc:
                record += 1 #ignore this record and proceed to the next
                goodRecords -= 1
                continue
                
            # plot pixels with color data for this record
            colorIndex = ImageParams.DATA_SIZE.value + 8  # start of color data
            self.outIndex = 0 # index into decompressed data
            while colorIndex < ImageParams.BUFFER_SIZE.value:
                # process pixel data for this color card (geoPaint always 80 cards wide)
                # NOTE: nextCardColors increments self.outIndex
                self.nextCardColors(self.decompressedBytes[colorIndex], 80, height) # all geoPaint images 80 cards wide
                colorIndex += 1
                self.card += 1
                if self.card == 80:  # end of card row
                    self.cardRow += 1
                    self.card = 0
                self.row = self.cardRow * 8  # top row, incremented by i
            record += 1

        if self.errors:
            message = f"Data errors for {dirEntry.getDisplayFileName()}:"
            for e in self.errors:
                match e:
                    case CorruptType.MISSING_DATA:
                        message += "\n  missing data"
                    case CorruptType.EXTRA_DATA:
                        message += "\n  extra data"
                    case CorruptType.NULL_BYTE:
                        message += "\n  null compression byte"
            QMessageBox.warning(None, "Warning", message, QMessageBox.StandardButton.Ok)

        # create pixmap double size
        self.rawImage = self.rawImage.scaled(QSize(640 * 2, height * 2))
        pixmap = QPixmap.fromImage(self.rawImage)

        # if some records were unreadable, shorten the pixmap
        logging.debug(f"good records/total: {goodRecords}/{records}")
        if goodRecords < records:
            logging.debug(f"resizing pixmap height from {records * 32} to {goodRecords * 32}")
            pixmap = pixmap.copy(0, 0, 640, goodRecords * 32)
        return pixmap

    def decompressGeoPaintRecord(self, inBuffer, outBuffer, bitmapSize):
        """
        Decompress a single record to the combined pixel and color buffer.
        :param inBuffer: The bytes to decompress.
        :param outBuffer: Buffer for decompressed data.
        :param outIndex: Index into output buffer.
        :param bitmapSize: Size of output buffer.
        """
        outIndex = 0; bytesDecompressed = 0
        while bytesDecompressed < bitmapSize:
            if self.inputIndex >= len(inBuffer):
                logging.debug(f"Missing data: input index is {self.inputIndex}, VLIR record is {len(inBuffer)}")
                self.errors.add(CorruptType.EXTRA_DATA)
                message = "This image is corrupt (extra data)."
                raise Exception(message)

            cmd = inBuffer[self.inputIndex]
            self.inputIndex += 1  # point to data
            if not cmd:
                self.errors.add(CorruptType.NULL_BYTE)
                message = "This image is corrupt (null compression byte)."
                logging.debug(message)
                raise Exception(message)

            if cmd < 64:  # next "count" bytes are data
                count = cmd
                #logging.debug(f"cmd is {cmd}, next {count} bytes are data")
                if bytesDecompressed + count > bitmapSize: # as the saying goes, "this should never happen"
                    logging.debug(f"extra data: expected {bitmapSize}, got {bytesDecompressed + count}")
                    self.errors.add(CorruptType.EXTRA_DATA)
                    message = "This image is corrupt (extra data)."
                    raise Exception(message)
                bytesDecompressed += count
                j = 0
                while j < count:
                    if self.inputIndex + j >= len(inBuffer):
                        logging.debug(f"Missing data: index is {self.inputIndex + j}, VLIR buffer size is {len(inBuffer)}")
                        self.errors.add(CorruptType.MISSING_DATA)
                        message = "This image is corrupt (missing data)."
                        raise Exception(message)
                    outBuffer[outIndex] = inBuffer[self.inputIndex + j]
                    outIndex += 1
                    j += 1
                self.inputIndex += count  # point to next command

            elif cmd < 128:  # repeat next card (eight bytes) "count" times
                count = cmd - 64
                #logging.debug(f"cmd is {cmd}, repeat next card {count} times")
                if bytesDecompressed + (count * 8) > bitmapSize: # as the saying goes, "this should never happen"
                    logging.debug(f"extra data: expected {bitmapSize}, got {bytesDecompressed + (count * 8)}")
                    self.errors.add(CorruptType.EXTRA_DATA)
                    message = "This image is corrupt (extra data)."
                    raise Exception(message)
                bytesDecompressed += count * 8
                j = 0
                while j < count:
                    k = 0
                    while k < 8:
                        if self.inputIndex + k >= len(inBuffer):
                            logging.debug(f"Missing data: index is {self.inputIndex + k}, buffer size is {len(inBuffer)}")
                            self.errors.add(CorruptType.EXTRA_DATA)
                            message = "This image is corrupt (extra data)."
                            raise Exception(message)
                        outBuffer[outIndex] = inBuffer[self.inputIndex + k]
                        outIndex += 1
                        k += 1
                    j += 1
                self.inputIndex += 8  # point to next command

            else:  # repeat next byte "count" times
                count = cmd - 128
                #logging.debug(f"cmd is {cmd}, repeat next byte {count} times")
                if bytesDecompressed + count > bitmapSize: # as the saying goes, "this should never happen"
                    # example: GEOMANDA.D64, file DICKSMACART
                    self.errors.add(CorruptType.EXTRA_DATA)
                    logging.debug(f"extra data: expected {bitmapSize}, got {bytesDecompressed} + {count} = {bytesDecompressed + count}")
                    count = bitmapSize - bytesDecompressed
                bytesDecompressed += count
                j = 0
                while j < count:
                    if self.inputIndex >= len(inBuffer):
                        logging.debug(f"Missing data: index is {self.inputIndex}, buffer size is {len(inBuffer)}")
                        self.errors.add(CorruptType.MISSING_DATA)
                        message = "This image is corrupt (missing data)."
                        raise Exception(message)
                    outBuffer[outIndex] = inBuffer[self.inputIndex]
                    outIndex += 1
                    j += 1
                self.inputIndex += 1  # point to next command

    def nextCardColors(self, colors, width, height):
        """
        Plot the 64 pixels of a card (8 rows).
        :param colors: Card's color data (4 bits each foreground/background).
        :param width: The width of the bitmap in bytes.
        :param height: The height of the bitmap in pixels.
        """
        fg = (colors & 0xf0) >> 4
        bg = colors & 0x0f
        i = 0
        while i < 8:  # i is line (byte) counter within card
            pixelData = self.decompressedBytes[self.outIndex]
            j = 0
            while j < 8:  # j is bits within this card line
                mask = (1 << (7 - j))
                data = fg if pixelData & mask else bg
                try:
                    x = (self.card * 8) + j
                    y = self.row + i
                    if x >= width * 8 or y >= height:
                        logging.debug(f"OUT OF RANGE {width * 8} X {height}! x: {x}, y: {y}")
                    try:
                        self.rawImage.setPixel(QPoint(x, y), data)
                    except Exeption as pxc:
                        raise pxc
                except Exception as exc:
                    logging.exception(exc)
                j += 1
            i += 1
            self.outIndex += 1

class PhotoScrap:
    """
    Class modeling a photo scrap.
    """
    def __init__(self, width: int, height: int, bitmap: QPixmap, name: str = None):
        self.width = width
        self.height = height
        self.bitmap = bitmap
        self.name = name
