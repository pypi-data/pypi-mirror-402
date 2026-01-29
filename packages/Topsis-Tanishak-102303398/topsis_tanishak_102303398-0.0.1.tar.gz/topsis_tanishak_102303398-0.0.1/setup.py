from setuptools import setup, find_packages

setup(
    name="Topsis-Tanishak-102303398",
    version="0.0.1",
    author="Tanishak",
    author_email="tanishakbansal@gmail.com",
    description="A Python package implementing TOPSIS for multi-criteria decision making",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_tanishak_102303398.topsis:topsis"
        ]
    },
)
