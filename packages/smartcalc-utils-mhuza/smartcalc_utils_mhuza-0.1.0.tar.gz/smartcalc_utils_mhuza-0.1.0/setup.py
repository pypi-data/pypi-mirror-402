from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smartcalc-utils",  # Package name on PyPI (use your unique name if taken)
    version="0.1.0",
    author="Your Name",  # REPLACE with your actual name
    author_email="your.email@example.com",  # REPLACE with your email
    description="Smart calculation utilities for finance and statistical analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smartcalc-utils",  # Optional
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    keywords="finance calculator statistics emi compound-interest percentile",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/smartcalc-utils/issues",
        "Source": "https://github.com/yourusername/smartcalc-utils",
    },
)