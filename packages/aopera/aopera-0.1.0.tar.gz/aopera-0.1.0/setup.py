
from setuptools import setup, find_packages
 
setup(name='aopera',
      version='0.1.0',
      url='https://gitlab.lam.fr/lam-grd-public/aopera.git',
      license='See LICENSE file',
      author='Romain JL Fetick (ONERA Chatillon, France)',
      author_email='romain.fetick@onera.fr',
      description='analytical AO residuals PSD and PSF generation',
      packages=find_packages(exclude=['example','test-script','test-unit','make-exe']),
      requires=['numpy','scipy'])
