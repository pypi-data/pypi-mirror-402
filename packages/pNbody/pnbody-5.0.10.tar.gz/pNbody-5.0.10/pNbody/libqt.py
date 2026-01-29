#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libqt.py
#  brief:     PyQT4 interface
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage


import numpy as np
from .libutil import *

from PIL import ImageQt


def rgb(r, g, b):
    # use qRgb to pack the colors, and then turn the resulting long
    # into a negative integer with the same bit pattern.
    return (QtGui.qRgb(r, g, b) & 0xffffff) - 0x1000000


class QNumarrayImage(QtGui.QImage):
    """
    QNumarrayImage class
    """

    def __init__(self, data, palette_name):

        format = QtGui.QImage.Format_Indexed8

        # include the palette
        palette = Palette(palette_name)

        # data = data*0+64
        data = data.astype(np.uint8)

        # give the right form
        shape = data.shape
        data = np.transpose(data)
        data = np.ravel(data)
        data.shape = shape

        self.__data = data.tostring()

        # init object
        QtGui.QImage.__init__(
            self,
            self.__data,
            data.shape[0],
            data.shape[1],
            format)

        # color table
        colortable = []
        for i in range(256):
            colortable.append(QtGui.qRgb(palette.r[i], palette.g[i], palette.b[i]))
        self.setColorTable(colortable)


def qtplot(mat, palette='light'):
    """
    plot a matrix using qt
    """

    app = QtGui.QApplication(sys.argv)

    imageLabel = QtGui.QLabel()
    imageLabel.setScaledContents(True)

    matint, mn, mx, cd = set_ranges(
        mat, scale='lin', mn=None, mx=None, cd=None)

    # without qt
    imageQt = QNumarrayImage(matint, palette)

    # using PIL
    # imagePIL = get_image(matint,name=None,palette_name=palette)
    # imageQt  = ImageQt.ImageQt(imagePIL)

    imageLabel.setPixmap(QtGui.QPixmap.fromImage(imageQt))

    imageLabel.show()
    sys.exit(app.exec_())




class DisplayWindow(QWidget):

    def __init__(self,imagePIL):
        super().__init__()
                
        # this no longer works !!!
        #imageQt = ImageQt.ImageQt(imagePIL)   
        #self.im = QPixmap.fromImage(imageQt)
        
        # so, do things in detail through numpy
        imagePIL = imagePIL.convert("RGB")
        data = np.array(imagePIL)
        qimage = QImage(data.data, data.shape[1], data.shape[0], data.strides[0], QImage.Format_RGB888);
        self.im = QPixmap(qimage)


        self.label = QLabel()
        self.label.setPixmap(self.im)

        self.grid = QGridLayout()
        self.grid.addWidget(self.label,1,1)
        self.setLayout(self.grid)

        self.setGeometry(50,50,320,200)
        self.setWindowTitle("PyQT show image")
        self.show()


def display(imagePIL):

  app = QApplication(sys.argv)
  ex = DisplayWindow(imagePIL)
  app.exec_()
  #sys.exit(app.exec_())











