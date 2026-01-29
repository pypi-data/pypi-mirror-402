from setuptools import setup, find_packages

setup(
    name="topsis-gurkirat-102303256",  # Now all lowercase
    version="1.1.1",                  # Updated version
    author="Gurkirat Singh",
    description="A professional command-line tool for TOPSIS decision analysis.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pandas', 
        'numpy', 
        'openpyxl'                   # Added to support .xlsx files
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis_pkg.topsis:topsis',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)