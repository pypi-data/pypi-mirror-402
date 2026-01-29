from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
setup(
    name="gamebanking",
    version="1.1.1",
    author="CorruptDragon24",
    description="gamebanking is a module that makes coding currency in games easier.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://www.youtube.com/@CorruptDragon24",
    python_requires=">=3.6",
)