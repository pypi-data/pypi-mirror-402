from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Topsis-Ananya-102303594",
    version="0.2",
    author="Ananya Singh",
    author_email="ananya@example.com",
    description="A Python package implementing the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ananya_102303594.topsis:topsis"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.8",
)

