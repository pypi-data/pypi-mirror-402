from setuptools import setup, find_packages

setup(
    name="maxnetlib",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.18.0"
    ],
    author="Daniel Tayade",
    author_email="danieltayade2004@gmail.com",
    description="A simple Python library to implement MaxNet neural network for finding the winning neuron",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dandan-077/maxnetlib",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    python_requires=">=3.7",
)

