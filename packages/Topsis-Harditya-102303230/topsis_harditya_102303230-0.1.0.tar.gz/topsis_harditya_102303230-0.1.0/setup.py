from setuptools import setup, find_packages

setup(
    name="Topsis-Harditya-102303230",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_harditya_102303230.main:run"
        ]
    },
    author="Harditya",
    description="TOPSIS implementation with CLI support",
)