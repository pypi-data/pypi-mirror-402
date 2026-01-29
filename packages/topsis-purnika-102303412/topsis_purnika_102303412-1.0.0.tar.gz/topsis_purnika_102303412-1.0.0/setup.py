from setuptools import setup, find_packages

setup(
    name="Topsis-Purnika-102303412",
    version="1.0.0",
    author="Purnika Malhotra",
    author_email="purnikamalhotra53@gmail.com",
    description="TOPSIS implementation as a Python package",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=TOPSIS_MAIN.topsis:main'
        ]
    }
)
