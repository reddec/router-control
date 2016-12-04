from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rvcm',
    version='1.0.7',
    description='Control RV6688BCM router',
    long_description=long_description,
    url='https://github.com/reddec/router-control',
    author='Baryshnikov Alexander',
    author_email='dev@baryshnikov.net',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='RV6688BCM router-control gpon rvcm',
    install_requires=['click>=6.4', 'requests>=2.10', 'lxml>=3.6'],
    entry_points={
        'console_scripts': [
            'rvcm=rvcm.__main__:main'
        ]
    }
)
