#----------------------------------------------------------------------
# Name:        wx.lib.wxcairo
# Purpose:     Glue code to allow either the PyCairo package or the
#              cairocffi package to be used with a wx.DC as the cairo
#              surface.
#
# Author:      Robin Dunn
#
# Created:     3-Sept-2008
# Copyright:   (c) 2008-2020 by Total Control Software
# Licence:     wxWindows license
#
# Tags:        phoenix-port, py3-port
# (c) 2022 Zombie
#----------------------------------------------------------------------

"""
This package provides some glue code that allows the Cairo library to draw
directly on :class:`wx.DC` objects, convert to/from :class:`wx.Bitmap`
objects, etc. using either the PyCairo or the newer cairocffi Cairo wrappers.
In Cairo terms, the DC is the drawing surface.  The ``CairoContextFromDC``
function in this module will return an instance of the Cairo Context class
that is ready for drawing, using the native cairo surface type for the current
platform.

.. note:: Be sure to import ``wx.lib.wxcairo`` before importing the ``cairo``
   module.

To use Cairo with wxPython you will need to have a few dependencies installed.
On Linux systems, you already have them after installing the packages needed to
build the complete wxPython-zombie.

On Windows, dependencies will be installed with wxPython-zombie.
"""

#----------------------------------------------------------------------------

import wx

# Import our glue functions for either cairocffi or pycairo, depending on
# which is installed.
try:
    # Use cairocffi first if it is available
    from .wx_cairocffi import _ContextFromDC, _FontFaceFromFont
    import cairo
except ImportError:
    try:
        # otherwise use pycairo
        from .wx_pycairo import _ContextFromDC, _FontFaceFromFont
        import cairo
    except ImportError:
        # or provide some exception raising stubs instead
        def _ContextFromDC(dc):
            raise NotImplementedError("Cairo wrappers not found")

        def _FontFaceFromFont(font):
            raise NotImplementedError("Cairo wrappers not found")

#----------------------------------------------------------------------------

def ContextFromDC(dc):
    """
    Creates and returns a ``cairo.Context`` object using the :class:`wx.DC` as
    the surface.  (Only window, client, paint and memory DC's are allowed at
    this time.)
    """
    return _ContextFromDC(dc)


def FontFaceFromFont(font):
    """
    Creates and returns a ``cairo.FontFace`` object from the native
    information in a :class:`wx.Font`.
    """
    return _FontFaceFromFont(font)

#----------------------------------------------------------------------------
# wxBitmap <--> ImageSurface

def BitmapFromImageSurface(surface):
    """
    Create a :class:`wx.Bitmap` from a Cairo ``ImageSurface``.
    """
    format = surface.get_format()
    if format not in [cairo.FORMAT_ARGB32, cairo.FORMAT_RGB24]:
        raise TypeError("Unsupported format")

    width  = surface.get_width()
    height = surface.get_height()
    stride = surface.get_stride()
    data   = surface.get_data()
    if format == cairo.FORMAT_ARGB32:
        fmt = wx.BitmapBufferFormat_ARGB32
    else:
        fmt = wx.BitmapBufferFormat_RGB32

    bmp = wx.Bitmap(width, height, 32)
    bmp.CopyFromBuffer(data, fmt, stride)
    return bmp


def ImageSurfaceFromBitmap(bitmap):
    """
    Create a Cairo ``ImageSurface`` from a :class:`wx.Bitmap`
    """
    width, height = bitmap.GetSize()
    if bitmap.ConvertToImage().HasAlpha():
        format = cairo.FORMAT_ARGB32
        fmt = wx.BitmapBufferFormat_ARGB32
    else:
        format = cairo.FORMAT_RGB24
        fmt = wx.BitmapBufferFormat_RGB32

    try:
        stride = cairo.ImageSurface.format_stride_for_width(format, width)
    except AttributeError:
        stride = width * 4

    surface = cairo.ImageSurface(format, width, height)
    bitmap.CopyToBuffer(surface.get_data(), fmt, stride)
    surface.mark_dirty()
    return surface

#----------------------------------------------------------------------------
