from setuptools import setup

setup(name='ReflectX',
      version='1.0.0',
      description='Reflected Light planet models',
      url='https://reflectx.readthedocs.io/en/latest/',
      author='Logan Pearce',
      author_email='lapearce@umich.edu',
      #license='MIT',
      install_requires=['numpy','scipy','astropy','matplotlib','xarray', 'h5netcdf', 'h5py'],
      packages=['ReflectX'],
      zip_safe=False)