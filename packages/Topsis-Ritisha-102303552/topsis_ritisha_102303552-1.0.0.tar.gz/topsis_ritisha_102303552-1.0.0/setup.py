from setuptools import setup, find_packages

setup(
    name="Topsis-Ritisha-102303552",
    version="1.0.0",
    author="Ritisha Sidana",
    author_email="rsidana1_be23@thapar.edu",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ritisha_102303552.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
