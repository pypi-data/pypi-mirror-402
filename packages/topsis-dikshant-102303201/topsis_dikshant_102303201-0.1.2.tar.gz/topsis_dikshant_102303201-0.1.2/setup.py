from setuptools import setup, find_packages

setup(
    name="topsis-dikshant-102303201",
    version="0.1.2",
    author="Dikshant",
    author_email="dikshantarora15@gmail.com",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_dikshant_102303201.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.7",
)
