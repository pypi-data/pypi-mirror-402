import pathlib
from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent

VERSION = '1.0.0'
PACKAGE_NAME = 'pickit-urv'
AUTHOR = 'Said Trujillo de León'
AUTHOR_EMAIL = '31ldts@gmail.com'
URL = 'https://github.com/31ldts'

LICENSE = (HERE / "LICENSE.txt").read_text(encoding='utf-8')
DESCRIPTION = "Librería para seleccionar y analizar interacciones moleculares según su actividad de unión (pIC50)."
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding='utf-8')
LONG_DESC_TYPE = "text/markdown"

# Paquetes necesarios que se instalarán automáticamente si no están presentes
INSTALL_REQUIRES = [
    'matplotlib>=3.1.0',    # Para pyplot y MaxNLocator
    'mplcursors>=0.6',       # Para la interactividad en gráficos
    'pandas>=2.0.0',         # Para pd (DataFrames y análisis de datos)
    'numpy>=2.0.0',          # Para np (aunque pandas lo incluye, es bueno especificarlo)
    'seaborn>=0.13.2',       # Para sns (visualizaciones estadísticas)
    'openpyxl>=3.1.5',       # Para load_workbook y PatternFill (manejo de Excel)
]

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESC_TYPE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    install_requires=INSTALL_REQUIRES,
    license=LICENSE,
    packages=find_packages(),
    include_package_data=True
)

