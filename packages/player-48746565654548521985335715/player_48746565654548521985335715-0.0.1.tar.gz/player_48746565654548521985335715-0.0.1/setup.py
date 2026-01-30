import setuptools
from pathlib import Path

long_desc = Path("README.md").read_text()

#generar empaquetado
setuptools.setup(
    name = "player_48746565654548521985335715",
    version="0.0.1",
    long_description=long_desc,
    packages=setuptools.find_packages(exclude=["mocks","tests"]) #colocamos cuales paquete no subir
)