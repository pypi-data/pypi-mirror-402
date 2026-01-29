from setuptools import setup, find_packages

setup(
    name="Topsis-Bhaumik",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis.__main__:main"
        ]
    },
    author="Bhaumik Verma",
    description="TOPSIS implementation for multi-criteria decision analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Bhaumik181/TOPSIS",
    license="MIT"
)
