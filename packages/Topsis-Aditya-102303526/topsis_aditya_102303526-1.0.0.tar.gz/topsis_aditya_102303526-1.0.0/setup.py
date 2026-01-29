from setuptools import setup, find_packages

setup(
    name='Topsis-Aditya-102303526',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'openpyxl'
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis_aditya.topsis:topsis'
        ]
    },
    author='Aditya',
    description='TOPSIS implementation as a Python package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
