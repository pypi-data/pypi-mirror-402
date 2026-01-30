"""Setup configuration for tcbs package"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from package
version = {}
with open(os.path.join("tcbs", "__init__.py"), "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="tcbs",
    version=version.get("__version__", "0.1.0"),
    author="TCBS SDK Contributors",
    author_email="cskh@tcbs.com.vn",
    description="Lightweight Python SDK for Techcom Securities (TCBS) iFlash Open API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tcbs/tcbs-python-sdk",
    project_urls={
        "Bug Reports": "https://github.com/tcbs/tcbs-python-sdk/issues",
        "Documentation": "https://developers.tcbs.com.vn",
        "Source": "https://github.com/tcbs/tcbs-python-sdk",
    },
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
    },
    keywords="tcbs techcom securities trading stocks derivatives vietnam api iflash",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
