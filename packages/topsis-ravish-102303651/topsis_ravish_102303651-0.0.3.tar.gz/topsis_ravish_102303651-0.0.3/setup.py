from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = this_directory.joinpath("README.md").read_text(encoding="utf-8")

setup(
    name="topsis-ravish-102303651",
    version="0.0.3",
    author="ravish",
    author_email="sharmaravish77400@gmail.com",
    description="TOPSIS implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    include_package_data=True,
    license="MIT License",
    license_files=("LICENSE",),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ravish.topsis:main"
        ]
    },
)
