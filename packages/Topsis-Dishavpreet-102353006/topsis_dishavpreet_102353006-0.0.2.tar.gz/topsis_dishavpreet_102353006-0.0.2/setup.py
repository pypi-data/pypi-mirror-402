from setuptools import setup, find_packages

setup(
    name="Topsis-Dishavpreet-102353006",          # FirstName-RollNumber
    version="0.0.2",
    author="Dishavpreet",
    author_email="dishav1202@gmail.com",
    description="Implementation of TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
