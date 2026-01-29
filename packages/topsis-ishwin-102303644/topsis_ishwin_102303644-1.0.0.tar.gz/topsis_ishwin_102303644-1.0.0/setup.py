from setuptools import setup, find_packages

setup(
    name="topsis-ishwin-102303644",
    version="1.0.0",
    author="Ishwin",
    author_email="syal.ishwin@gmail.com",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy", "openpyxl"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ishwin_1023036446.topsis:topsis"
        ]
    },
)
