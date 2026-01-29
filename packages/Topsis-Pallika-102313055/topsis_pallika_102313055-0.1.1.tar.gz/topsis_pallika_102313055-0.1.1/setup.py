from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Pallika-102313055",
    version="0.1.1",  # bumped version
    author="Pallika",
    author_email="pallika@gmail.com",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_pallika_102313055.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
