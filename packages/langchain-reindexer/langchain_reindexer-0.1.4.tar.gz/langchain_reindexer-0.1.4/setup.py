"""Setup script for local development and testing."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="langchain-community-reindexer",
    version="0.1.4",
    description="Reindexer vector store integration for LangChain",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Parviz Mirzoev",
    author_email="parviz.mirzoev@restream.ru",
    packages=find_packages(),
    install_requires=["langchain-core>=0.1.0", "pyreindexer>=0.5.0", "numpy>=2.0.2"],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    python_requires=">=3.9",
)
