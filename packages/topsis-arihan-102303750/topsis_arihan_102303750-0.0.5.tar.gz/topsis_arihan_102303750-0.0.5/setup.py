from setuptools import setup, find_packages

setup(
    name="topsis-arihan-102303750",
    version="0.0.5",
    author="Arihan Andotra",
    author_email="aandotra_be23@thapar.edu",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_arihan_102303750.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
