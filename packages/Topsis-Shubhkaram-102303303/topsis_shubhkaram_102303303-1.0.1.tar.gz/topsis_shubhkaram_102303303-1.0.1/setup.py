from setuptools import setup, find_packages

setup(
    name="Topsis-Shubhkaram-102303303",   
    version="1.0.1",
    author="Shubhkaram Singh",
    author_email="shubhkaram2724@gmail.com",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_shubhkaram_102303303.topsis:run",
        ],
    },
)
