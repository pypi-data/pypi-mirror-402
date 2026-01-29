# setup.py
from setuptools import setup, Extension, find_packages

import shutil, glob, os

#c_dir = 'src/csclib'
#os.makedirs(c_dir, exist_ok = True)
#
#for filename in glob.glob('../../c/*.h'):
#  print('copy', filename, 'to', c_dir)
#  shutil.copy(filename, c_dir)
#shutil.copy('../../README.md', '.')

setup(name = 'csclib',
      ext_modules = [
          Extension(
              name = 'ccsclib',
              sources = ['src/csclib/pycsclib.c'],
              extra_compile_args=['-O3', '-Wno-unused-function', '-Wno-unused-variable'],
          )],
      package_data={"csclib": ["*.h"]}
)
