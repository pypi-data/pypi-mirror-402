from setuptools import setup, find_packages

setup(
    name="topsis-prashant-102353011",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_prashant.topsis:topsis"
        ]
    },
    author="Prashant Gagneja",
    description="TOPSIS implementation in Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)
