from setuptools import setup, find_packages

setup(
    name="Topsis-Ananya-102303594",
    version="0.1",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ananya_102303594.topsis:topsis"
        ]
    },
    author="Ananya Singh",
    description="TOPSIS command line package",
)
