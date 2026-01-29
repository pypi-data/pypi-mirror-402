from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agredadb",
    version="2.0.0",
    description="Official Python Client for AgredaDB - The Limitless Database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Luis Eduardo Agreda Gonzalez",
    author_email="luisagreda.ai@gmail.com",
    url="https://github.com/luisagreda-aidev/agredadb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "ml": ["torch>=1.9.0", "numpy>=1.19.0"],
        "dev": ["pytest>=6.0.0", "pytest-cov>=2.10.0"],
    },
)
