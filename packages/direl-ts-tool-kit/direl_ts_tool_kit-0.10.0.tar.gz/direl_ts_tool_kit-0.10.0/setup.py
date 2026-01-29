from setuptools import setup, find_packages

setup(
    name="direl-ts-tool-kit",
    version="0.10.0",
    description="A toolbox for time series analysis and visualization.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Diego Restrepo-Leal",
    author_email="diegorestrepoleal@gmail.com",
    url="https://gitlab.com/direl/direl_tool_kit",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "matplotlib>=3.0.0",
        "openpyxl",
        "seaborn",
        "scipy"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.8",
)
