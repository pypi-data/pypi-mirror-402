from setuptools import setup, find_packages

setup(
    name="Topsis-Ritigya-102303467",
    version="1.0.0",
    author="Ritigya",
    author_email="rsingh7_be23@thapar.edu",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "topsis=topsis_ritigya_102303467.cli:main"
        ]
    },
)
