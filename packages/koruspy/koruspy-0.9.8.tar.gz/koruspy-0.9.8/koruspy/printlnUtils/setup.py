# koruspy/printlnUtils/setup.py

from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        Extension(
            name="cythonprintln",                # nome do módulo gerado
            sources=["cythonprintln.pyx"],       # arquivo .pyx
        ),
        language_level="3",                      # força Python 3
        annotate=True                            # gera HTML para ver otimizações
    )
)