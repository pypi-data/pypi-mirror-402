from setuptools import setup, find_packages

# Package setup configuration
setup(
    name="Topsis-Khushi-102303610",   
    version="1.0.0",
    author="Khushi",
    author_email="khushigoyal1808@gmail.com",  
    description="A Python package for TOPSIS multi-criteria decision making method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    python_requires=">=3.7",
)
