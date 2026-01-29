from setuptools import setup, find_packages

setup(
    name="Topsis-Priyal-102303563",
    version="0.0.2",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
    author="Priyal Gupta",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
)
