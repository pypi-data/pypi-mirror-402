from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="securevault-pqc",  # Name on PyPI (securevault might be taken)
    version="0.1.0",
    author="Reggy Mane",
    author_email="your.email@example.com",
    description="Post-quantum file encryption using ML-KEM-768 + X25519",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/securevault",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/securevault/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    py_modules=["securevault"],
    python_requires=">=3.9",
    install_requires=[
        "liboqs-python>=0.8.0",
        "cryptography>=41.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "securevault=securevault:cli",  # Creates 'securevault' command
        ],
    },
)