from setuptools import setup, find_packages

setup(
    name="Topsis-Avneet-102303289",
    version="1.0.1",
    author="Avneet Sandhu",
    author_email="your_email@gmail.com",
    description="TOPSIS command line tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.cli:main"

        ]
    },
)
