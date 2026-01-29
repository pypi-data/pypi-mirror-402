from setuptools import setup, find_packages

setup(
    name="Topsis-Pariza-102303391",
    version="0.0.1",
    author="Pariza Singh Kandol",
    description="TOPSIS implementation as a command-line Python package",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
