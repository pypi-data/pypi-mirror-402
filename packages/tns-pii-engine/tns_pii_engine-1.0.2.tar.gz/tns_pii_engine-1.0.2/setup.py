from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tns-pii-engine",
    version="1.0.2",
    description="Enterprise PII Masking, Tokenization & Encryption Module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Naveenkumar Koppala",
    author_email="naveenkumar.k@tnsservices.com",
    license="MIT",
    packages=find_packages(exclude=["tests*", "unwanted*"]),
    package_data={
        "pii_engine": ["config/*.json"],
    },
    install_requires=[
        "cryptography>=3.4.8",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "fastapi": ["fastapi>=0.68.0", "uvicorn>=0.15.0"],
        "dev": ["pytest>=7.0.0", "black>=22.0.0"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
)
