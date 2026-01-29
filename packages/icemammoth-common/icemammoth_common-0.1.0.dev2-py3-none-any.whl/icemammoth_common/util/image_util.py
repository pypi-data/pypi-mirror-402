
# -*- coding: utf-8 -*-

import io
from PIL import Image

def convertToJPGImageBytes(imageBytes:bytes) -> bytes:
    # 打开图像
    image = Image.open(io.BytesIO(imageBytes))
    # 将图像转换为JPG格式
    jpgImageBytesIO = io.BytesIO()
    image.convert("RGB").save(jpgImageBytesIO,'JPEG')
    return jpgImageBytesIO.getvalue()

def fetchImageType(imageBytes:bytes) -> str:
        # typeMap = {
        #      'FFD8':'JPG',
        #      '424D':'BMP',
        #      '474946':'GIF',
        #      '89504E470D0A1A0A':'PNG',
        # }
        # sig = ""
        # for i in range(8):
        #     sig += hex(imageBytes[i]).upper()[2:]
        #     imageType = typeMap.get(sig)
        #     if imageType:
        #          return imageType
        
        # return None
        '''
            Image format

            RGB : SGI ImgLib Files
            GIF : GIF 87a and 89a Files
            PBM : Portable Bitmap Files
            PGM : Portable Graymap Files
            PPM : Portable Pixmap Files
            TIFF : TIFF Files
            RAST : Sun Raster Files
            XBM : X Bitmap Files
            JPEG : JPEG data in JFIF or Exif formats
            BMP : BMP files
            PNG : Portable Network Graphics
            WEBP : WebP files
            EXR : OpenEXR Files
        '''
        image = Image.open(io.BytesIO(imageBytes))
        return image.format
   
def fetchImageSize(imageBytes:bytes) -> (int,int):
    image =  Image.open(io.BytesIO(imageBytes))
    return (image.width,image.height)

def resetImageSize(imageBytes:bytes,width:int,height:int) -> bytes:
     image = Image.open(io.BytesIO(imageBytes))
     imageType = image.format
     jpgImageBytesIO = io.BytesIO()
     image.resize((width,height),Image.Resampling.NEAREST).save(jpgImageBytesIO, imageType , optimize=True, quality=95)
     return jpgImageBytesIO.getvalue()