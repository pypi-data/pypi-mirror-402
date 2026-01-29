import setuptools
from pathlib import Path


long_description = Path('README.md').read_text()
setuptools.setup(
    name='estoesunaprueba',
    version='0.0.1',
    long_description=long_description,
    packages=setuptools.find_packages(
        exclude=['mocks, tests'] #Paquetes que no quiero publicar
    )
)