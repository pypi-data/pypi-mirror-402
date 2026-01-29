from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pillowstrap",  # Check pypi.org if this name is free!
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Bootstrap-like semantic wrapper for Python Pillow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pillowstrap", # Optional but good
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "Pillow>=10.0.0",
    ],
)