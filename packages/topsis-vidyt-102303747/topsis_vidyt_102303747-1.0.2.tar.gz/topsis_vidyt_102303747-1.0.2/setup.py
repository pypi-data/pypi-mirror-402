from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="topsis-vidyt-102303747",
    version="1.0.2",
    author="Vidyt",
    author_email="vidyt102303747@example.com",
    description="TOPSIS decision-making algorithm implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VidytBhudolia/UCS654-102303747",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.0.0",
        "openpyxl>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_package.__main__:main",
        ],
    },
)
