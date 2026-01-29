from setuptools import setup, find_packages

setup(
    name="Topsis-Nimish-102483077",
    version="1.0.2",
    author="Nimish",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis = topsis_nimish_102483077.topsis:main"
        ]
    },
)
