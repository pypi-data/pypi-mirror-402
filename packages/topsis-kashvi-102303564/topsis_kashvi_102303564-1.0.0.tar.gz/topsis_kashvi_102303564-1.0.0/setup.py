from setuptools import setup, find_packages

setup(
    name="topsis_kashvi_102303564",
    version="1.0.0",
    author="Kashvi Aggarwal",
    author_email="kaggarwal_be23@thapar.edu",
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
