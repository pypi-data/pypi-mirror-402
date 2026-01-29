from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis-purnika-102303412",
    version="1.0.1",   # 🔴 VERSION BUMP IS MUST
    author="Purnika Malhotra",
    author_email="purnikamalhotra53@gmail.com",
    description="This package implements the TOPSIS method for multi-criteria decision making using a command-line interface. It allows users to rank alternatives from a CSV file by specifying custom weights and impacts. The package includes input validation and generates a ranked output file efficiently. It is designed for academic and practical decision-analysis use.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=TOPSIS_MAIN.topsis:main"
        ]
    },
    python_requires=">=3.8",
)

