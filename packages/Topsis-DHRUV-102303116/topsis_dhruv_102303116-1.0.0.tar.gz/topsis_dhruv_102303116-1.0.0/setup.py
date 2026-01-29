from setuptools import setup, find_packages

setup(
    name="Topsis-DHRUV-102303116",
    version="1.0.0",
    author="Dhruv",
    author_email="dverma2_be23@thapar.edu",
    description="A Python package for TOPSIS implementation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_dhruv_102303116.topsis:main"

        ]
    },
    python_requires=">=3.7",
)
