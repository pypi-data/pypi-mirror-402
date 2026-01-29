from setuptools import setup, find_packages

setup(
    name="Topsis-Tushargarg-102303674",
    version="0.1.1",
    author="Tushar",
    author_email="tgarg3_be23@thapar.edu",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy" ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_tushargarg_102303674.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
