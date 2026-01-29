#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      Movie.py
#  brief:     Movie functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import string

import numpy as np

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImagePalette
from PIL import ImageFont


class Movie:
    """
    a Movie class
    """

    ##########################
    def __init__(self, name, mode=None):
        ##########################

        self.name = name
        self.mode = mode
        self.starttime = 0.0
        self.stoptime = 0.0
        self.dt = 0.0
        self.npic = 0
        self.numByte = 0
        self.numLine = 0
        self.headerlength = 0
        self.blocksize = 0
        self.filmsize = 0
        self.shape = (0, 0)

        self.current_npic = 0

        # self.film

    ##########################

    def open(self, mode='rb', readall=0):
        ##########################
        """
        open a file
        """

        numByte = 256

        # open the file
        self.film = open(self.name, mode)

        ###############################################
        # read the header and find numByte and numLine
        ###############################################

        self.header = self.film.read(256)

        if len(self.header) != 256:
            raise Exception("film length < 256, ,stop")

        self.film.seek(240)

        str1 = self.film.read(8)
        str2 = self.film.read(8)

        if (str1 != "	" and str2 != "        "):
            self.numByte = int(str1)
            self.numLine = int(str2)
        else:
            self.numByte = 256
            self.numLine = 192

        if self.mode == 'RGB':
            self.numLine = self.numLine * 3

        if self.numByte < 256:
            self.headerlength = 256
        else:
            self.headerlength = self.numByte

        ###############################################
        # read the header and find numByte and numLine
        ###############################################

        self.blocksize = int(self.numLine * self.numByte + self.headerlength)
        self.shape = (self.numByte, self.numLine)

        #############################
        # check film length
        #############################

        self.film.seek(0, 2)
        self.filmsize = self.film.tell()
        self.film.seek(0)

        np.fmod(self.filmsize, self.blocksize)

        self.npic = self.filmsize // self.blocksize

        #############################
        # read times
        #############################

        self.film.seek(0)
        self.starttime = float(self.film.read(self.headerlength)[:8])
        self.film.seek(0)

        self.moveto(self.npic)
        self.stoptime = float(self.film.read(self.headerlength)[:8])
        self.film.seek(0)

        if self.npic > 1:
            self.dt = (self.stoptime - self.starttime) / self.npic
        else:
            self.dt = 0

        self.current_npic = 0


    ##########################
    def info(self):
        ##########################
        """
        give info
        """

        print(("""
    -- %s  --

    initial time	    : %8.3f
    final   time	    : %8.3f
    dt  		    : %8.3f
    number of images	    : %d
    number of collumns      : %d
    number of lines	    : %d
    length of header	    : %d
    length of block         : %d
    length of film          : %d

    current_npic            : %d
    """ % (self.name, self.starttime, self.stoptime, self.dt, self.npic, self.numByte, self.numLine, self.headerlength, self.blocksize, self.filmsize, self.current_npic)))

    ##########################

    def new(self, numByte, numLine):
        ##########################

        self.numByte = numByte
        self.numLine = numLine

        if self.numByte < 256:
            self.headerlength = 256
        else:
            self.headerlength = self.numByte

        self.film = open(self.name, "wb")

    ##########################
    def close(self):
        ##########################

        self.film.close()

    ##########################
    def read_one(self, mode=None):
        ##########################

        # reading next label
        time = self.film.read(self.headerlength)

        if len(time) == self.headerlength:

            # record starttime
            self.current_time = float(time[:8])

            # reading next data
            data = self.film.read(self.numByte * self.numLine)
            if len(data) == self.numByte * self.numLine:

                self.current_image = data

                if mode == "array":
                    return np.reshape(np.fromstring(data, np.uint8),
                                   (self.numLine, self.numByte))
                elif mode == "image":
                    return Image.frombytes("P", 
                        (self.numByte, self.numLine), data)
                else:
                    return data

    ##########################
    def read_one_with_time(self, mode=None):
        ##########################

        # reading next label
        time = self.film.read(self.headerlength)

        if len(time) == self.headerlength:

            # record starttime
            self.current_time = float(time[:8])

            shape = (self.numByte, self.numLine)

            if mode == "array":
                data = self.film.read(self.numByte * self.numLine)
                return time, np.reshape(
                    np.fromstring(
                        data, 'b'), (self.numLine, self.numByte))

            elif mode == "image":
                data = self.film.read(self.numByte * self.numLine)
                return time, Image.frombytes("P", shape, data)

            elif mode == "image_rgb":

                dataR = self.film.read(self.numByte * self.numLine)
                self.film.read(self.headerlength)
                dataG = self.film.read(self.numByte * self.numLine)
                self.film.read(self.headerlength)
                dataB = self.film.read(self.numByte * self.numLine)

                imageR = Image.frombytes("L", shape, dataR)
                imageG = Image.frombytes("L", shape, dataG)
                imageB = Image.frombytes("L", shape, dataB)

                return time, Image.merge('RGB', (imageR, imageG, imageB))

            else:
                data = self.film.read(self.numByte * self.numLine)
                return time, data

        else:
            return None, None

    ##########################
    def read(self, skip=0, mode='array'):
        ##########################
        """
        skip =  0 	: read image at the current position
        skip =  1	: skip an image
        skip = -1   : read the image before (go back)
        skip = -2   : skip an image before  (go back)
        """

        # move relative to the current position
        try:
            self.film.seek(skip * self.blocksize, 1)
        except IOError:
            self.moveto(0)
            return -1, 0, -1

        self.current_npic = self.film.tell() // self.blocksize

        if self.current_npic > self.npic - 1:
            self.moveto(self.npic)
            return -2, self.current_npic, -2

        # reading next label
        time = self.film.read(self.headerlength)

        # record starttime
        self.current_time = float(time[:8])

        if mode == "array":
            data = self.film.read(self.numByte * self.numLine)
            return self.current_time, self.current_npic, np.transpose(
                np.reshape(np.fromstring(data, 'b'), (self.numLine, self.numByte)))

        elif mode == "image":
            data = self.film.read(self.numByte * self.numLine)
            return self.current_time, self.current_npic, Image.frombytes(
                "P", self.shape, data)

        elif mode == "image_rgb":

            dataR = self.film.read(self.numByte * self.numLine)
            self.film.read(self.headerlength)
            dataG = self.film.read(self.numByte * self.numLine)
            self.film.read(self.headerlength)
            dataB = self.film.read(self.numByte * self.numLine)

            imageR = Image.frombytes("L", self.shape, dataR)
            imageG = Image.frombytes("L", self.shape, dataG)
            imageB = Image.frombytes("L", self.shape, dataB)

            return self.current_time, self.current_npic, Image.merge(
                'RGB', (imageR, imageG, imageB))

        else:
            data = self.film.read(self.numByte * self.numLine)
            return self.current_time, self.current_npic, data

    ##########################
    def moveto(self, npic):
        ##########################

        npic = min(npic, self.npic - 1)
        npic = max(npic, 0)

        current_npic = self.film.tell() // self.blocksize
        dnpic = npic - current_npic
        db = dnpic * self.blocksize
        self.film.seek(db, 1)

        self.current_npic = self.film.tell() // self.blocksize

    ###########################
    def write_pic(self, time, data):
        ###########################

        recsize = self.numByte

        record = b'%8.3f' % time

        s1 = bytes.ljust(record, 240)
        s2 = bytes.ljust(bytes(self.numByte), 8)
        if self.mode == 'RGB':
            s3 = bytes.ljust(bytes(self.numLine // 3), 8)
        else:
            s3 = bytes.ljust(bytes(self.numLine), 8)
        record = s1 + s2 + s3
        record = bytes.ljust(record, recsize)

        self.film.write(record)
        self.film.write(data)

    ###########################
    def write_pic_rgb(self, time, dataR, dataG, dataB):
        ###########################

        recsize = self.numByte

        record = '%8.3f' % time

        s1 = str.ljust(record, 240)
        s2 = str.ljust(repr(self.numByte), 8)
        s3 = str.ljust(repr(self.numLine), 8)
        record = s1 + s2 + s3
        record = str.ljust(record, recsize)

        self.film.write(record)
        self.film.write(dataR)
        self.film.write(dataG)
        self.film.write(dataB)

    ###########################
    def get_img(self, data):
        ###########################
        """
        can be replaced by read_one with option "image"
        """
        shape = (self.numByte, self.numLine)
        image = Image.frombytes("P", shape, data)
        return image


###################################
def append_h(numByte, numLine, datas):
    ###################################

    newdata = b''

    # loop over the lines
    for j in range(numLine):

        j1 = j * numByte 		# set cursors
        j2 = j1 + numByte

        # loop over the images
        for data in datas:

            newdata = newdata + data[j1:j2]  # simply sum

    return newdata
