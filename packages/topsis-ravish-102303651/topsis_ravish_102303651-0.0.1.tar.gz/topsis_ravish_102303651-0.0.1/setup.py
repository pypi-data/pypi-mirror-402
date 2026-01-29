from setuptools import setup, find_packages

setup(
    name="topsis-ravish-102303651",
    version="0.0.1",
    author="ravish",
    author_email="sharmaravish77400@gmail.com",
    description="TOPSIS implementation",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ravish.topsis:main"
        ]
    },
)
