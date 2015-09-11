# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2015, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
import os
import unittest

from pyramid import httpexceptions
from pyramid import testing as pyramid_testing
from pyramid.request import Request

from saxon import Saxon
from subprocess import CalledProcessError

try:
    OEREXPORTS_PATH = os.environ['OEREXPORTS_PATH']
except KeyError:
    raise RuntimeError("You must set the OEREXPORTS_PATH environment "
                       "variable to the location of oer.exports.")
SETTINGS = {
    'oerexports_path': os.path.abspath(OEREXPORTS_PATH),
    '_saxon_jar_filepath': os.path.abspath(os.path.join(
        OEREXPORTS_PATH, 'lib', 'saxon9he.jar')),
    '_mathml2svg_xsl_filepath': os.path.abspath(os.path.join(
        OEREXPORTS_PATH, 'xslt2', 'math2svg-in-docbook.xsl')),
    }

MATHML = """<math xmlns="http://www.w3.org/1998/Math/MathML"><mstyle displaystyle="true"><mrow><mi>sin</mi><mrow><mo>(</mo><mi>x</mi><mo>)</mo></mrow></mrow></mstyle></math>"""
# This isn't really invalid, but the pmml2svg process trips over it.
INVALID_MATHML = """<math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow> <mi>x</mi> <mo>=</mo> <mfrac> <mrow> <mo>&#8722;<!-- &#8722; --></mo> <mi>b</mi> <mo>&#177;<!-- &#177; --></mo> <msqrt> <msup> <mi>b</mi> <mn>2</mn> </msup> <mo>&#8722;<!-- &#8722; --></mo> <mn>4</mn> <mi>a</mi> <mi>c</mi> </msqrt> </mrow> <mrow> <mn>2</mn> <mi>a</mi> </mrow> </mfrac> </mrow><annotation encoding="math/tex">x=\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}</annotation></semantics></math>"""


def load_data(file_name):
    with open(file_name, 'r') as f:
        data = f. read()
    return data

SVG = load_data('test_data/svg.xml')

UNBOUNDED_MATHML = load_data('test_data/unbounded_mathml.xml')

class Test_Saxon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._saxon = Saxon()

    @classmethod
    def tearDownClass(cls):
        cls._saxon.stop()

    def setUp(self):
        self.saxon = self._saxon

    def test_class_setup(self):
        pass

    def test_multiple_saxon_calls(self):
        for i in range(0, 10):
            returned_svg,err = self.saxon.convert(MATHML)
            returned_svg=returned_svg.strip('\t\r\n ')
            expected_svg = SVG.strip('\t\r\n ')
            self.assertEqual(returned_svg, expected_svg)

    def test_invalid_mathml_error(self):
        self.addCleanup(self.setUpClass)
        with self.assertRaises(CalledProcessError):
            self.saxon.convert(INVALID_MATHML)

    def test_unbounded_mathml(self):
#        self.addCleanup(self.setUpClass)
#        with self.assertRaises(CalledProcessError):
        (out,err)=self.saxon.convert(MATHML)
        self.assertIn("LOG: INFO: MathML2SVG",err)
        (out,err)=self.saxon.convert(UNBOUNDED_MATHML)
        self.assertIn("LOG: INFO: MathML2SVG",err)
        (out,err)=self.saxon.convert(MATHML)
        self.assertIn("WARNING: Cannot determine bounding box for glyph",err) 
        #self.saxon.convert(MATHML)


    @unittest.skip("Run this test to generate performance graphics")
    def test_performance_gain(self):
        """Compare Saxon class to subprocss performance"""
        import math
        import timeit
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        x=[]
        y_single=[]
        y_multi=[]
        for iterations in [int(math.pow(2,i)) for i in range(0,5)]:
            stmt="saxon.convert('{}')".format(MATHML)
            setup='from saxon import Saxon;saxon=Saxon()'
            single_process_call=timeit.timeit(stmt,setup,number=iterations)
            setup="import subprocess;cmd = 'java -jar {_saxon_jar_filepath} -s:- -xsl:{_mathml2svg_xsl_filepath}'".format(**SETTINGS)
            stmt="p = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True);p.communicate('{}')".format(MATHML)
            multiple_process_call=timeit.timeit(stmt,setup,number=iterations)
            self.assertLess(single_process_call,multiple_process_call)
            x.append(iterations)
            y_single.append(single_process_call)
            y_multi.append(multiple_process_call)

        slope_single, intercept_single = np.polyfit(x,y_single,1)
        slope_multi, intercept_multi = np.polyfit(x,y_multi,1)
        plt.title("Estimated {0:.1f}x performance gain ".format(slope_multi/slope_single))
        
        plot_single, =plt.plot(x, y_single)
        plot_multi, =plt.plot(x, y_multi)
        plt.legend([plot_single,plot_multi],['single process','multiple processes'],loc=0)
        plt.axis([0,max(x),0,max(max(y_single),max(y_multi))])
        plt.ylabel("Time (s)")
        plt.xlabel("Loop iterations")
        plt.show()        

         

class SVGGeneration(unittest.TestCase):

    def setUp(self):
        self.settings = SETTINGS.copy()

    @property
    def target(self):
        from cnxmathml2svg import mathml2svg
        return mathml2svg

    def test_success(self):
        mathml = MATHML.encode('utf-8')
        expected = b"""\
<svg xmlns="http://www.w3.org/2000/svg" xmlns:pmml2svg="https://sourceforge.net/projects/pmml2svg/" version="1.1" width="27.009999999999998pt" height="12.524999999999999pt" viewBox="0 0 27.009999999999998 12.524999999999999"><metadata><pmml2svg:baseline-shift>3.6949999999999985</pmml2svg:baseline-shift></metadata><g stroke="none" fill="#000000" text-rendering="optimizeLegibility" font-family="STIXGeneral,STIXSizeOneSym,STIXIntegralsD,STIXIntegralsSm,STIXIntegralsUp,STIXIntegralsUpD,STIXIntegralsUpSm,STIXNonUnicode,STIXSizeFiveSym,STIXSizeFourSym,STIXSizeThreeSym,STIXSizeTwoSym,STIXVariants"><g xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" style="font-family: STIXGeneral,STIXSizeOneSym,STIXIntegralsD,STIXIntegralsSm,STIXIntegralsUp,STIXIntegralsUpD,STIXIntegralsUpSm,STIXNonUnicode,STIXSizeFiveSym,STIXSizeFourSym,STIXSizeThreeSym,STIXSizeTwoSym,STIXVariants; fill: ; background-color: transparent; "><g style="font-family: STIXGeneral,STIXSizeOneSym,STIXIntegralsD,STIXIntegralsSm,STIXIntegralsUp,STIXIntegralsUpD,STIXIntegralsUpSm,STIXNonUnicode,STIXSizeFiveSym,STIXSizeFourSym,STIXSizeThreeSym,STIXSizeTwoSym,STIXVariants; fill: ; background-color: transparent; "><g style="font-family: STIXGeneral,STIXSizeOneSym,STIXIntegralsD,STIXIntegralsSm,STIXIntegralsUp,STIXIntegralsUpD,STIXIntegralsUpSm,STIXNonUnicode,STIXSizeFiveSym,STIXSizeFourSym,STIXSizeThreeSym,STIXSizeTwoSym,STIXVariants; fill: ; background-color: transparent; "><text style="font-family: STIXGeneral, STIXSizeOneSym, STIXIntegralsD, STIXIntegralsSm, STIXIntegralsUp, STIXIntegralsUpD, STIXIntegralsUpSm, STIXNonUnicode, STIXSizeFiveSym, STIXSizeFourSym, STIXSizeThreeSym, STIXSizeTwoSym, STIXVariants; fill: black; background-color: transparent; " x="2" y="8.83" font-size="10">sin</text><g style="font-family: STIXGeneral,STIXSizeOneSym,STIXIntegralsD,STIXIntegralsSm,STIXIntegralsUp,STIXIntegralsUpD,STIXIntegralsUpSm,STIXNonUnicode,STIXSizeFiveSym,STIXSizeFourSym,STIXSizeThreeSym,STIXSizeTwoSym,STIXVariants; fill: ; background-color: transparent; "><g style="font-family: STIXGeneral, STIXSizeOneSym, STIXIntegralsD, STIXIntegralsSm, STIXIntegralsUp, STIXIntegralsUpD, STIXIntegralsUpSm, STIXNonUnicode, STIXSizeFiveSym, STIXSizeFourSym, STIXSizeThreeSym, STIXSizeTwoSym, STIXVariants; fill: black; background-color: transparent; "><text x="13.65" y="8.764999999999999" font-size="10">(</text></g><text style="font-family: STIXGeneral, STIXSizeOneSym, STIXIntegralsD, STIXIntegralsSm, STIXIntegralsUp, STIXIntegralsUpD, STIXIntegralsUpSm, STIXNonUnicode, STIXSizeFiveSym, STIXSizeFourSym, STIXSizeThreeSym, STIXSizeTwoSym, STIXVariants; font-style: italic; fill: black; background-color: transparent; " x="17.23" y="8.83" font-size="10">x</text><g style="font-family: STIXGeneral, STIXSizeOneSym, STIXIntegralsD, STIXIntegralsSm, STIXIntegralsUp, STIXIntegralsUpD, STIXIntegralsUpSm, STIXNonUnicode, STIXSizeFiveSym, STIXSizeFourSym, STIXSizeThreeSym, STIXSizeTwoSym, STIXVariants; fill: black; background-color: transparent; "><text x="21.689999999999998" y="8.764999999999999" font-size="10">)</text></g></g></g></g></g></g></svg>"""
        svg = self.target(mathml, self.settings)
        self.assertEqual(svg, expected)


class Views(unittest.TestCase):

    def setUp(self):
        self.config = pyramid_testing.setUp(settings=SETTINGS)

    def tearDown(self):
        pyramid_testing.tearDown()

    def test_success_w_form_post(self):
        """Test MathML2SVG post using a text based form value."""
        request = Request.blank('/', POST={'MathML': MATHML})

        from cnxmathml2svg import convert
        response = convert(request)

        self.assertIn(b'<svg ', response.body)
        self.assertEqual(response.content_type, 'image/svg+xml')

    def test_success_w_multiform_post(self):
        """Test MathML2SVG post using a multipart form value."""
        request = Request.blank('/', POST={'MathML': ('mathml.xml', MATHML)})

        from cnxmathml2svg import convert
        response = convert(request)

        self.assertIn(b'<svg ', response.body)
        self.assertEqual(response.content_type, 'image/svg+xml')

    def test_missing_parameters(self):
        """Test response for a Bad Request when parameters are missing."""
        request = Request.blank('/')

        from cnxmathml2svg import convert
        with self.assertRaises(httpexceptions.HTTPBadRequest):
            convert(request)

    def test_transform_failure(self):
        """Test MathML2SVG post with content that won't transform,
        but contains valid xml and MathML elements.
        """
        request = Request.blank('/', POST={'MathML': INVALID_MATHML})

        from cnxmathml2svg import convert
        exception_cls = httpexceptions.HTTPInternalServerError
        with self.assertRaises(exception_cls) as caught_exc:
            convert(request)

        exception = caught_exc.exception
        self.assertIn(b'Error reported by XML parser: ', exception.comment)
