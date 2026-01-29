import setuptools

from setuptools import setup, find_packages

setup(
    name='topsis-raunaqmittal',  # Unique package name
    version='0.1.0',
    author='Raunaq Mittal',
    author_email='raunaqmittal2004@gmail.com',
    description='TOPSIS implementation for multi-criteria decision making',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/raunaqmittal/Topsis-Package',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
