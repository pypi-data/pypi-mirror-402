from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wesamoyo",  
    version="1.0.7", 
    author="Houndtid Labs",
    author_email="houndtidai@gmail.com",
    description="Official SDK for Wesamoyo-293M-MoE: 293M parameter Mixture-of-Experts transformer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/houndtidlabs",
    packages=["wesamoyo"],
    install_requires=[
        "transformers>=4.40.0",
        "torch>=2.4.1",
        "safetensors>=0.4.5"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)