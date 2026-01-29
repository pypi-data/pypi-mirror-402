from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="topsis-sargun-102303367",
    version="0.1.1",
    author="sargun kaur",
    author_email="skaur4_be23@thapar.edu",
    description="A Python package implementing TOPSIS for multi-criteria decision making",
    long_description=long_description,            
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/Topsis-Trishti-102313056/",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
