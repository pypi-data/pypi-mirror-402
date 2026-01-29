from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Vihaan-102303658",
    version="1.1.1",
    author="Vihaan Agarwal",                   
    author_email="dpsvih12036@gmail.com", 
    description="A Python package to implement TOPSIS for MCDM.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Vihaan001/topsis", 
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "pandas",
        "numpy",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_Vihaan_102303658.topsis:main",
        ],
    },
)