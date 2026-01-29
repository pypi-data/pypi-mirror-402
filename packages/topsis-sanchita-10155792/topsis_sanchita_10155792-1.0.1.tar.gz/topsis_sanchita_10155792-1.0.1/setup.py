from setuptools import setup, find_packages

setup(
    name="topsis-sanchita-10155792",
    version="1.0.1",
    author="Sanchita Sharma",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
