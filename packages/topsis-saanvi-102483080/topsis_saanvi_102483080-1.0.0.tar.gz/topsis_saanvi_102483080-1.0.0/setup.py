from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis-saanvi-102483080",
    version="1.0.0",   # production version
    author="Saanvi Wadhwa",
    author_email="your_email@gmail.com",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)

