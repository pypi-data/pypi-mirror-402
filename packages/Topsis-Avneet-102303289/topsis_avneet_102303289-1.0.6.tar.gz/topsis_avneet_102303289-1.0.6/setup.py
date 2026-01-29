from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Topsis-Avneet-102303289",
    version="1.0.6",   
    author="Avneet Sandhu",
    author_email="your_email@gmail.com",
    description="TOPSIS command line tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.cli:main"
        ]
    },
)

