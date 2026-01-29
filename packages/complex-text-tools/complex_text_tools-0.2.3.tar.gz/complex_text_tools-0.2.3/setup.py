from setuptools import setup, find_packages
import os

# 读取README文件内容
def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
        return fh.read()

setup(
    name="complex-text-tools",
    version="0.2.2",
    author="mooremok",
    author_email="mooremok@163.com",
    description="A package for processing complex text with mixed Chinese and English characters",
    long_description=read_long_description() if os.path.exists("README.md") else "A package for processing complex text with mixed Chinese and English characters",
    long_description_content_type="text/markdown",
    url="https://github.com/mooremok/complex-text-tools",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.6",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
        ],
    },
)