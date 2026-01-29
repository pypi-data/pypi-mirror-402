from setuptools import setup, find_packages

VERSION = '0.0.3'
DESCRIPTION = 'Python pkg for TOPSIS method for MCMD problems '

setup(
    name="Topsis_Rupam_102317201",
    version=VERSION,
    author="Rupam",
    author_email="rbiswas_be23@thapar.edu",
    description=DESCRIPTION,
    long_description=open("readme.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ProfessionalYapper0311",
    packages=find_packages(),
    install_requires=['pandas' ,'numpy'],
    keywords=['python', 'topsis', 'topsis-rupam', 'topsis-rupam-102317201'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "topsis=Topsis_Rupam_102317201.topsis:main",
        ],
    }
)