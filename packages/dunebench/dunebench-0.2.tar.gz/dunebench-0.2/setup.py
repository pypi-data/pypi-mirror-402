from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dunebench",
    version="0.2",
    packages=find_packages(),

    author="Rudransh Joshi",
    author_email="rudranshseptmber@gmail.com",
    description="dunebench – a lightweight evaluation tool for llama.cpp models",
    long_description="dunebench is a CLI-based evaluation framework built on llama-cpp-python.",
    long_description_content_type="text/markdown",


    install_requires=[
        "llama-cpp-python",
        "datasets",
        "tqdm"
    ],

    entry_points={
        'console_scripts': [
            'dune-eval=dunebench:main',
        ],
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.8",
)
