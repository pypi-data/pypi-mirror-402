from __future__ import division, print_function
from setuptools import setup

_version = '2.0.4'

setup(name='seawolf',
      version=_version,
      description='Tools for matplotlib plots',
      author='Bayron Torres Gordillo',
      author_email='torres.bayron@gmail.com',
      long_description_content_type='text/markdown',
      install_requires=['numpy','pandas','seaborn','matplotlib'],
      packages=['seawolf'],
      include_package_data=True,
      license = 'BSD',
      platforms = ["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
      python_requires='>=3.5'
    )