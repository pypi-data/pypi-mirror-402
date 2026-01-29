from setuptools import setup, find_packages

setup(
    name="topsis-shubhkarman-102303661",
    version="1.0.2",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_shubhkarman_102303661.main:topsis"
        ]
    },
    author="Shubhkarman Singh",
    description="A command-line implementation of TOPSIS for multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
