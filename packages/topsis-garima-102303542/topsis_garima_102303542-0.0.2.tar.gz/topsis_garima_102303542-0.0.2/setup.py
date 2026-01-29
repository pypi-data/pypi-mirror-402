from setuptools import setup, find_packages

setup(
    name="topsis_garima_102303542",
    version="0.0.2",
    author="Garima Singla",
    author_email="garimasingla732@gmail.com",
    description="TOPSIS implementation in Python (Command Line Tool)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
