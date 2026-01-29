from setuptools import setup, find_packages

setup(
    name="Topsis-Ashpreet-102303263",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=topsis_ashpreet_102303263.topsis:run'
        ]
    },
)
