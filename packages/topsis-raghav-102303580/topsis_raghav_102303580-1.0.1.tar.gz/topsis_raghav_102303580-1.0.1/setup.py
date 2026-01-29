from setuptools import setup, find_packages

setup(
    name="topsis-raghav-102303580",
    version="1.0.1",
    author="Raghav",
    author_email="raghavchhabra291984@gmail.com",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_raghav_102303580.topsis:main"
        ]
    },
)
