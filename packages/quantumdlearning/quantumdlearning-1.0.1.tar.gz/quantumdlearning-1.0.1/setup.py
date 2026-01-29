"""
QuantumDLearning: A framework for quantum machine learning that integrates latest research results
in quantum computing and deep learning.
"""

from setuptools import setup, find_packages

# 读取README文件
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="quantumdlearning",
    version="1.0.1",
    author="QuantumDLearning Team",
    author_email="quantumdlearning@example.com",
    description="A framework for quantum machine learning that integrates latest research results in quantum computing and deep learning.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pylint>=2.14.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "tqdm>=4.60.0"
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "tqdm>=4.60.0"
        ],
        "viz": [
            "qiskit>=0.40.0",
            "bayesian-optimization>=1.4.0"
        ],
        "all": [
            "qiskit>=0.40.0",
            "bayesian-optimization>=1.4.0",
            "tqdm>=4.60.0"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
    url="https://github.com/quantumdlearning/quantumdlearning",
    project_urls={
        "Bug Reports": "https://github.com/quantumdlearning/quantumdlearning/issues",
        "Source": "https://github.com/quantumdlearning/quantumdlearning",
    },
    keywords="quantum machine learning quantum computing neural networks deep learning",
    license="MIT",
)
