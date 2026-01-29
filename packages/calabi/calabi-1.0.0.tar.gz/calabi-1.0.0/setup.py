from setuptools import setup, find_packages
import os
import io

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calabi",
    version="1.0.0",
    author="Roshan Raghavander",
    author_email="roshanraghavander@gmail.com",
    description="A novel approach to LLM compression using Calabi-Yau manifolds",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RoshanRaghavander/Calabi",
    packages=find_packages(include=['calabi', 'calabi_yau_compression', 'deployment']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.12.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
        "transformers": [
            "transformers>=4.0.0",
            "accelerate>=0.20.0",
        ],
        "examples": [
            "transformers>=4.0.0",
            "datasets>=2.0.0",
            "accelerate>=0.20.0",
        ],
    },
    keywords="llm-compression, deep-learning, pytorch, geometric-deep-learning, calabi-yau, neural-networks, model-compression, huggingface, transformers, bert, gpt",
    project_urls={
        "Bug Reports": "https://github.com/RoshanRaghavander/Calabi/issues",
        "Source": "https://github.com/RoshanRaghavander/Calabi",
        "Documentation": "https://github.com/RoshanRaghavander/Calabi/blob/main/API_REFERENCE.md",
    },
    license="MIT",
    license_files=("LICENSE",),
    zip_safe=False,
)