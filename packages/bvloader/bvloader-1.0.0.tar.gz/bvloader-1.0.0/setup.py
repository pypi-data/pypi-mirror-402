from setuptools import setup, find_packages

setup(
    name="bvloader",
    version="1.0.0",
    author="JACK",
    author_email="gsksvsksksj@gmail.com",
    description="Light loader library that fetches and runs BV.py remotely",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/zrvvr4h4hgey34g-prog/shiny-umbrella",
    packages=find_packages(),
    install_requires=["requests"],
    python_requires=">=3.7",
)