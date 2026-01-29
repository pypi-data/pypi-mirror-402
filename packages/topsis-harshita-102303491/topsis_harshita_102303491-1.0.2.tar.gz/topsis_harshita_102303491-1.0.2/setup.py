from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="topsis-harshita-102303491",
    version="1.0.2",
    author="Harshita Goyal",
    author_email="harshitagoyal1405@gmail.com",
    description="A Python package for TOPSIS decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_harshita_102303491.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
