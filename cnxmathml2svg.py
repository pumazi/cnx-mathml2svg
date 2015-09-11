# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2015, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
import os
import sys
import subprocess
from subprocess import CalledProcessError

from io import BytesIO

from lxml import etree
from pyramid import httpexceptions
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.threadlocal import get_current_registry

from saxon import Saxon

sax = None

__all__ = ('main',)


def mathml2svg(mathml, settings=None):
    """Returns an SVG from the given *mathml*."""
    global sax

    if settings is None:
        settings = get_current_registry().settings
    if sax is None:
        sax = Saxon(saxon_path=settings['_saxon_jar_filepath'],
                    math2svg_path=settings['_mathml2svg_xsl_filepath'])

    (out,err) = sax.convert(mathml)

    if "WARNING" in err:
         sys.stderr.write(err)
         if "Cannot determine bounding box for glyph" in err:
             sax.stop()
             sax = Saxon(saxon_path=settings['_saxon_jar_filepath'],
                         math2svg_path=settings['_mathml2svg_xsl_filepath'])
        
    parser = etree.XMLParser(recover=True)
    try:
        xml = etree.parse(BytesIO(out), parser)
    except etree.XMLSyntaxError:
        raise ValueError(err)

    svg = etree.tostring(xml)
    return svg

def convert(request):
    """Convert the POST'd MathML to SVG"""
    try:
        mathml = request.POST['MathML']
    except KeyError:
        raise httpexceptions.HTTPBadRequest("Missing required parameters")
    if request.content_type.startswith('multipart/form-data'):
        mathml = mathml.file.read()
    if isinstance(mathml, str):
        mathml = mathml.encode('utf8')

    try:
        svg = mathml2svg(mathml)
    except ValueError as exc:
        raise httpexceptions.HTTPInternalServerError(*exc.args)
    except CalledProcessError:
        raise httpexceptions.HTTPInternalServerError(
            comment='Error reported by XML parser: ')
    return Response(svg, content_type="image/svg+xml")

def main(global_config, **settings):
    """Application factory"""
    # Ensure settings
    oerexports_path = settings.get('oer.exports_path')
    if not oerexports_path:
        raise RuntimeError("'oer.exports_path' is a required setting")
    # Derive a few settings from oer.exports_path
    settings['_saxon_jar_filepath'] = os.path.abspath(os.path.join(
        oerexports_path, 'lib', 'saxon9he.jar'))
    settings['_mathml2svg_xsl_filepath'] = os.path.abspath(os.path.join(
        oerexports_path, 'xslt2', 'math2svg-in-docbook.xsl'))

    config = Configurator(settings=settings)

    # Configure views
    config.add_route('convert', '/', request_method='POST')
    config.add_view(convert, route_name='convert')
    return config.make_wsgi_app()
