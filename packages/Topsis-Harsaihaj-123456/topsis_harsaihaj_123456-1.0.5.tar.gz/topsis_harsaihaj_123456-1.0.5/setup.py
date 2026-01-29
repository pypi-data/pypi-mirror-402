from setuptools import setup, find_packages
setup(
    name='Topsis-Harsaihaj-123456',
    version='1.0.5',
    author='Harsaihaj Singh',
    description='TOPSIS package',
    packages=find_packages(),
    install_requires=['numpy','pandas'],
    entry_points={'console_scripts':['topsis=topsis_harsaihaj.topsis:main']}
)
