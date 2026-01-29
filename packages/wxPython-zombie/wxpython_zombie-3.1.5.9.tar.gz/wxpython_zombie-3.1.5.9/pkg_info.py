import os


NAME             = 'wxPython-zombie'
VERSION          = '3.1.5.9'
TOP_LEVEL        = 'wx'
INSTALL_REQUIRES = ['numpy', 'Pillow', 'six']

if os.name != 'nt':
    INSTALL_REQUIRES.append('pycairo')
