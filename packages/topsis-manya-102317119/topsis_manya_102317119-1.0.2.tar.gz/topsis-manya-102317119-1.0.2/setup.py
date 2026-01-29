from setuptools import setup, find_packages

setup(
    name="topsis-manya-102317119",
    version="1.0.2",
    author="Manya Singh",
    author_email="yashmiki01@gmail.com",
    description="Python package for TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_manya_102317119.topsis:main",
        ],
    },
)
