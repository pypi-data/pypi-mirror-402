from setuptools import setup, find_packages
setup(
    name="topsis-himani-102303648",
    version="1.0.2",
    author="Himani Mahajan",
    author_email="",
    description="TOPSIS implementation as a command line tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
        "topsis=topsis_himani.topsis:run"
        ]
    },
)