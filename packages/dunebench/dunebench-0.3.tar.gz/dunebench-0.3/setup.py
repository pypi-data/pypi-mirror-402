from setuptools import setup, find_packages

# 1. Read the README file content into the variable
with open("README.md", "r", encoding="utf-8") as fh:
    long_description_content = fh.read()

setup(
    name="dunebench",
    version="0.3",  # <--- BUMPED VERSION (Required for re-upload)
    packages=find_packages(),

    author="Rudransh Joshi",
    author_email="rudranshseptmber@gmail.com",
    description="dunebench – a lightweight evaluation tool for llama.cpp models",
    
    # 2. Use the variable here (Don't overwrite it with a string!)
    long_description=long_description_content,
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