from setuptools import setup, find_packages
from pathlib import Path

# Read README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="topsis-keshav-102303520",
    version="1.0.1",   # ⬅️ version increased (IMPORTANT)
    author="Keshav Sharma",
    description="TOPSIS decision making package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_keshav_102303520.topsis:main"
        ]
    },
    python_requires=">=3.7",
)
