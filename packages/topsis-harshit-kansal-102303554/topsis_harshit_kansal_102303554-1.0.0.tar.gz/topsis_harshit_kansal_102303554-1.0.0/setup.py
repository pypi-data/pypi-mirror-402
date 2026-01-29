from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis-harshit-kansal-102303554",
    version="1.0.0",
    author="Harshit Kansal",
    author_email="hkansal_be23@thapar.edu",
    description="TOPSIS (MCDM) implementation for ranking alternatives using multiple criteria.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "topsis-hk=topsis_harshit_102303554.cli:main"
        ]
    },
)
