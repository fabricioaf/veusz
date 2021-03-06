#    Copyright (C) 2008 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################

from __future__ import division
import re

from ..compat import crange

def scalePDFMediaBox(text, pagewidth,
                     requiredwidth, requiredheight):
    """Take the PDF file text and adjust the page size.
    pagewidth: full page width
    requiredwidth: width we want
    requiredheight: height we want
    """
                     
    m = re.search(br'^/MediaBox \[([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\]$',
                  text, re.MULTILINE)

    box = [float(x) for x in m.groups()]
    widthfactor = box[2] / pagewidth
    newbox = ('/MediaBox [%i %i %i %i]' % (
            0, 
            int(box[3]-widthfactor*requiredheight),
            int(widthfactor*requiredwidth),
            int(box[3]))).encode('ascii')

    text = text[:m.start()] + newbox + text[m.end():]
    return text

def fixupPDFIndices(text):
    """Fixup index table in PDF.

    Basically, we need to find the start of each obj in the file
    These indices are then placed in an xref table at the end
    The index to the xref table is placed after a startxref
    """

    # find occurences of obj in string
    indices = {}
    for m in re.finditer(b'([0-9]+) 0 obj', text):
        index = int(m.group(1))
        indices[index] = m.start(0)

    # build up xref block (note trailing spaces)
    xref = [b'xref', ('0 %i' % (len(indices)+1)).encode('ascii'),
            b'0000000000 65535 f ']
    for i in crange(len(indices)):
        xref.append( ('%010i %05i n ' % (indices[i+1], 0)).encode('ascii') )
    xref.append(b'trailer\n')
    xref = b'\n'.join(xref)

    # replace current xref with this one
    xref_match = re.search(b'^xref\n.*trailer\n', text, re.DOTALL | re.MULTILINE)
    xref_index = xref_match.start(0)
    text = text[:xref_index] + xref + text[xref_match.end(0):]

    # put the correct index to the xref after startxref
    startxref_re = re.compile(b'^startxref\n[0-9]+\n', re.DOTALL | re.MULTILINE)
    text = startxref_re.sub( ('startxref\n%i\n' % xref_index).encode('ascii'),
                             text)

    return text
