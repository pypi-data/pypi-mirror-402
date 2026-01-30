BUILD_SCRIPT_TEMPLATE = r'''import os
import sys
from setuptools import Extension, setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext

source_root = sys.argv[1]
sys.argv = [sys.argv[0]] + sys.argv[2:]

extensions = []
full_filenames = %s

for full_filename in full_filenames:
    filename = full_filename[:-3].replace(os.path.sep, '.')
    abs_path = os.path.join(source_root, full_filename)
    extension = Extension(filename, [abs_path])
    extension.cython_c_in_temp = True
    extensions.append(extension)

py_ver = '%s'
if py_ver == '':
    py_ver = '3'
compiler_directives = {"language_level": py_ver, "annotation_typing": False}

setup(
    cmdclass={'build_ext': build_ext},
    packages=[],
    zip_safe=False,
    ext_modules=cythonize(
        extensions,
        nthreads=%s,
        build_dir=".py2dist/build_c",
        quiet=%s,
        compiler_directives=compiler_directives
    )
)
'''
