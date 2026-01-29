from setuptools import setup, find_packages

setup(
    name="Topsis-Charu-102303113",
    version="1.0.1",
    author="Charu",
    author_email="your_email@gmail.com",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
)
