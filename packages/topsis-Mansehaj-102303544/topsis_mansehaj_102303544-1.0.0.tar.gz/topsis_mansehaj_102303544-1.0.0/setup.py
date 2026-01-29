from setuptools import setup, find_packages

setup(
    name="topsis-Mansehaj-102303544",
    version="1.0.0",
    author="Mansehaj",
    description="TOPSIS implementation as a Python package",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
