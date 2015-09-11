import subprocess
import os
from os.path import exists, isfile, join, basename, abspath, dirname
SAXON_PATH = "./oer.exports/lib/saxon9he.jar"
DELIMINATOR = "END_OF_XML_BLOCK"
MATH2SVG_PATH = "./oer.exports/xslt2/math2svg-in-docbook.xsl"


class Saxon:

    def __init__(self, saxon_path=SAXON_PATH, math2svg_path=MATH2SVG_PATH):
        math2svg_path = abspath(math2svg_path)
        saxon_path = abspath(saxon_path)
        wrapper_file_path = join(
            dirname(saxon_path), "SaxonTransformWrapper.java")

        if not isfile(wrapper_file_path):
            raise IOError("File: {} not found".format(wrapper_file_path))
        if not isfile(saxon_path):
            raise IOError("File: {} not found".format(saxon_path))
        if not isfile(math2svg_path):
            raise IOError("File: {} not found".format(math2svg_path))

        try:
            subprocess.check_output("which javac".split())
        except subprocess.CalledProcessError as e:
            raise RuntimeError("'javac' command not found.  "
                               "Try running 'apt-get install openjdk-7-jdk'.")

        self.process_cmd = "javac -cp .:{0}:{1} SaxonTransformWrapper.java".format(
            saxon_path,
            dirname(saxon_path))

        self.process = subprocess.Popen(self.process_cmd.split(),
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        close_fds=True,
                                        cwd=dirname(saxon_path))
        self.process.wait()

        compiled_java_file = join(
            dirname(saxon_path), "SaxonTransformWrapper.class")

        if not isfile(compiled_java_file):
            raise RuntimeError("Compiled java file SaxonTransformWrapper.class not found."
                               "  Make sure 'javac' command is installed.")

        self.process_cmd = "java -cp saxon9he.jar:.:{0} SaxonTransformWrapper "\
            "-s:- -xsl:{1} -deliminator:{2}".format(saxon_path,
                                                    math2svg_path,
                                                    DELIMINATOR)

        self.process = subprocess.Popen(self.process_cmd.split(),
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        close_fds=True,
                                        cwd=dirname(saxon_path))

    def convert(self, xml):
        self.process.stdin.write(xml)
        self.process.stdin.write("\n" + DELIMINATOR + "\n")
        process_info = self.process.stderr.readline()
        if "LOG: INFO: MathML2SVG" in process_info:
            pass  # put logging info here if nessisary
        elif "Error" in process_info:
            error_info = process_info
            while process_info != '':
                process_info = self.process.stderr.readline()
                error_info = "".join([error_info, process_info])
            self.process.terminate()
            returncode = self.process.wait()
            raise subprocess.CalledProcessError(returncode,
                                                self.process_cmd,
                                                error_info)
        svg_line = ''
        svg_list = []
        while DELIMINATOR not in svg_line:
            svg_list.append(svg_line)
            svg_line = self.process.stdout.readline()
        self._flush()
        svg = '\n'.join(svg_list).strip()
        return (svg,process_info)

    def _flush(self):
        self.process.stdin.flush()
        self.process.stdout.flush()
        self.process.stderr.flush()

    def _close(self):
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()

    def stop(self):
        self._close()
        self.process.terminate()
        self.process.wait()

