from setuptools import setup

setup(
    name="Topsis-Shubhkaram-102303303",
    version="1.0.3",
    author="Shubhkaram Singh",
    author_email="YOUR_EMAIL@gmail.com",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=["topsis_shubhkaram_102303303"],   # 🔥 FIXED PACKAGE NAME
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_shubhkaram_102303303.topsis:run",
        ],
    },
)
