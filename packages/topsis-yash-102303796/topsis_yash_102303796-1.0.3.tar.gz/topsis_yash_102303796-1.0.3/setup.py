from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis_yash_102303796",
    version="1.0.3",
    author="Yash",
    author_email="yash@example.com",
    description="A Python package for TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_yash_102303796.topsis:main"
        ]
    },
    python_requires=">=3.6",
)
