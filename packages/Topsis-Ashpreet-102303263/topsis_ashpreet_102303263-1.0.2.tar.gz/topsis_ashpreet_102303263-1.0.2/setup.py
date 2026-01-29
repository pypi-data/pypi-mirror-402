from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="Topsis-Ashpreet-102303263",
    version="1.0.2",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'topsis=topsis_ashpreet_102303263.topsis:run'
        ]
    },
)
