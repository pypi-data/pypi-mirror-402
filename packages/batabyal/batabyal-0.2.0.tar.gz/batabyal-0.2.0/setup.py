from setuptools import setup, find_packages

setup(
    name="batabyal",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.20.0",
        "scikit-learn>=1.0.0"
    ],
    python_requires='>=3.10',
    author="T Batabyal",
    description="Data cleaning and automated ML model selection package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)