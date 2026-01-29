from setuptools import setup
from pathlib import Path

# Read README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="Topsis-Ansh-102303380",
    version="1.0.3",  # 🔴 VERSION MUST BE NEW
    author="Ansh Mahajan",
    author_email="anshakkimahajan@gmail.com",
    description="A Python implementation of TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["Topsis"],
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "Topsis=Topsis.__main__:main"
        ]
    },
    python_requires=">=3.7",
)