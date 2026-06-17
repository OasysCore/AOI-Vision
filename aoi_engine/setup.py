"""Core Engine: setup.py — Cython 编译支持
=========================================
生产部署:
  python setup.py build_ext --inplace
  → 生成 aoi_engine/defect.cpython-*.so (不可逆, 不可读)
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension("aoi_engine.defect", ["aoi_engine/defect.py"]),
    Extension("aoi_engine.vision", ["aoi_engine/vision.py"]),
    Extension("aoi_engine.calibration", ["aoi_engine/calibration.py"]),
]

setup(
    name="aoi-engine",
    version="0.2.0",
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
    include_dirs=[numpy.get_include()],
    zip_safe=False,
)
