from setuptools import setup, find_packages

setup(
    name="batabyal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5",
        "numpy>=1.24",
        "scikit-learn>=1.3"
    ],
    python_requires='>=3.10',
    author="T Batabyal",
    description="Data cleaning and automated ML model selection package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)