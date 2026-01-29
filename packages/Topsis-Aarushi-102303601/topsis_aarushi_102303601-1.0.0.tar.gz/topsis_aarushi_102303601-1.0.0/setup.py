from setuptools import setup, find_packages

setup(
    name="Topsis-Aarushi-102303601",
    version="1.0.0",
    author="Aarushi Rawal",
    author_email="aarushirawal@gmail.com",
    description="TOPSIS implementation using Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis-aarushi=topsis_aarushi.topsis:run"
        ]
    },
)
