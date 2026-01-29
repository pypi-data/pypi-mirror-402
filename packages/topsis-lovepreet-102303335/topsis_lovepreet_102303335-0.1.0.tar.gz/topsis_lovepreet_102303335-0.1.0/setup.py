from setuptools import setup, find_packages

setup(
    name="topsis-lovepreet-102303335",   # 🔴 UNIQUE name (change if needed)
    version="0.1.0",
    author="Lovepreet Bhatia",
    author_email="lovepreetbhatia178@gmail.com",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    python_requires=">=3.7",
)
