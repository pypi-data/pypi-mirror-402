from setuptools import setup, find_packages
import os

with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='osl_analysis',
    version='0.1.17',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    description='program for the analysis of physical processes of OSL curves',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='EDWIN JOEL PILCO QUISPE',
    author_email='edwinpilco10@gmail.com',
    url='https://pypi.org/project/OSL_ANALYSIS/',
    install_requires=[
        'numpy',
        'matplotlib',
        'scipy',
        'pandas',
        'prettytable',
        'ipython'
    ],
    python_requires='>=3.6',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
    ],
)