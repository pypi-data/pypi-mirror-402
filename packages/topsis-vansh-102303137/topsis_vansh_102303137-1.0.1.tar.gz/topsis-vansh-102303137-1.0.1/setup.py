from setuptools import setup, find_packages

setup(
    name="topsis-vansh-102303137",
    version="1.0.1",
    author="Vansh Garg",
    author_email="your_email@gmail.com",
    description="TOPSIS implementation for MCDM problems",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vansh_102303137.topsis:main"
        ]
    },
)
