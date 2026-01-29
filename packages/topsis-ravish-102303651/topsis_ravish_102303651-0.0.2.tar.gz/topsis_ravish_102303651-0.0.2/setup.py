from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
readme_text = this_directory.joinpath("README.md").read_text(encoding="utf-8")
license_text = ""
license_path = this_directory.joinpath("LICENSE")
if license_path.exists():
    license_text = license_path.read_text(encoding="utf-8")

long_description = readme_text + "\n\n## License\n\n" + license_text

setup(
    name="topsis-ravish-102303651",
    version="0.0.2",
    author="ravish",
    author_email="sharmaravish77400@gmail.com",
    description="TOPSIS implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "topsis=topsis_ravish.topsis:main"
        ]
    },
)
