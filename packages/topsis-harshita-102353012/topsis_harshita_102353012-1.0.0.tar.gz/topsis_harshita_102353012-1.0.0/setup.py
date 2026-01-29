from setuptools import setup, find_packages

setup(
    name="Topsis-Harshita-102353012",
    version="1.0.0",
    author="Harshita Goyal",
    author_email="harshitagoyal1405@gmail.com",
    description="A Python package for TOPSIS decision making",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_harshita_102303491.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
