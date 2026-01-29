from setuptools import setup, find_packages

setup(
    name="topsis-keshav-102303520",
    version="1.0.0",
    author="Keshav Sharma",
    description="TOPSIS decision making package",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_keshav_102303520.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
