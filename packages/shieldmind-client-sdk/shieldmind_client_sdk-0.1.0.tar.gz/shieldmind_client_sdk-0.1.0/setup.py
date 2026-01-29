"""
Setup script для Shieldmind Client SDK
"""
from setuptools import setup

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Shieldmind Client SDK - Легковесный клиент для валидации LLM запросов"

setup(
    name="shieldmind-client-sdk",
    version="0.1.0",
    author="Shieldmind",
    author_email="support@shieldmind.com",
    description="Легковесный Python SDK для валидации LLM запросов через Shieldmind API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shieldmind/shieldmind-pro",
    packages=["shieldmind_client_sdk"],
    package_dir={"": "."},  # Искать пакеты в текущей директории
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "shieldmind_client_sdk": ["py.typed"],
    },
)
