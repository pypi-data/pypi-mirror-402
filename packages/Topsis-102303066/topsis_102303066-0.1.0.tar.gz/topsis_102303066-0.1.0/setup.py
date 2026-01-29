import setuptools

from setuptools import setup, find_packages

setup(
    name='Topsis-102303066',  # Unique package name
    version='0.1.0',
    author='Raghav Garg',
    author_email='gargraghav1607@gmail.com',
    description='TOPSIS Algo implementation for multi-criteria decision',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/gargraghav0059/Topsis_102303066',
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
