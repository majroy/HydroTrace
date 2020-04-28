from os import path
import sys
from setuptools import setup, find_packages


setup(name = 'HydroTrace',
    version = '0.2post1',
    description = 'Hydrogen Trace Analysis Suite',
    long_description = 'https://github.com/majroy/HydroTrace',
    url = 'https://github.com/majroy/HydroTrace',
    author = 'M J Roy',
    author_email = 'matthew.roy@manchester.ac.uk',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Win32 (MS Windows)',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        ],

    install_requires=['numpy','scipy','pyyaml>=5.0','matplotlib','PyQt5>=5.13'],
    license = 'Creative Commons Attribution-Noncommercial-Share Alike license',
    keywords = 'Hydrogen, Trace, Curve-fit',
    packages=['HydroTrace', 'HydroTrace.meta'],
    package_data = {'HydroTrace' : ['README.MD',], 'HydroTrace.meta' : ['*.png',] },
    include_package_data=True

    )
