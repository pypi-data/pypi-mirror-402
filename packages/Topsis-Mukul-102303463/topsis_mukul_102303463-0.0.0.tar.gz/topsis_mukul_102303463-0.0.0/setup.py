from setuptools import setup, find_packages

setup(
    name="Topsis-Mukul-102303463",
    version="0.0.0",
    author="Mukul",
    author_email="mukulghai12@gmail.com",
    description="TOPSIS implementation with CLI support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_mukul_102303463.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
