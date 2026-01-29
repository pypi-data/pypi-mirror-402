from setuptools import setup, find_packages

setup(
    name="topsis_vansh_102353012",
    version="1.0.0",
    author="Vansh Garg",
    author_email="vanshgarg1635@gmail.com",
    description="A Python package for TOPSIS decision making",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vansh_102353012.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
