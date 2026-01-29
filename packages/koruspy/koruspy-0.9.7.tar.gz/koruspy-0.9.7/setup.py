from setuptools import setup, Extension
from Cython.Build import cythonize
import platform
import sys

# Flags de otimização
if platform.system() == "Windows":
    compile_args = ['/O2', '/Ot']
else:
    compile_args = ['-O3', '-march=native']

ext_modules = [
    Extension(
        "cythonprintln",
        sources=["./koruspy/printlnUtils/cythonprintln.pyx"],
        extra_compile_args=compile_args,
        # Isso ajuda o C a encontrar os arquivos do Python
        include_dirs=[sys.prefix + '/include'] 
    )
]

setup(
    name="printlnUtils",
    ext_modules=cythonize(ext_modules, compiler_directives={
        'language_level': "3",
        'boundscheck': False,
        'wraparound': False,
        'initializedcheck': False, # Ganhe mais um pouco de velocidade aqui
        'nonecheck': False         # E aqui também
    })
)
