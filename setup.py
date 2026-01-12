from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="clearscript",
    version="0.1.0",
    author="ClearScript Contributors",
    description="A compiler that uses C-style code to make a more readable InfiltrationEngine StateScript",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/centralstandardtime/ClearScript",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Compilers",
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
        # No external dependencies for initial version
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "clearscript=clearscript.cli:main",
        ],
    },
)
