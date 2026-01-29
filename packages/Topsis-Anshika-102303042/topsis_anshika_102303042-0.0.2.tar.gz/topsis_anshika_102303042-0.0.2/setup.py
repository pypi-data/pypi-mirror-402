from setuptools import setup, find_packages

setup(
    name="Topsis-Anshika-102303042",
    version="0.0.2",
    author="Anshika",
    author_email="anshika.aggarwal05@gmail.com",
    description="A Python package for TOPSIS implementation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_anshika_102303042.topsis:topsis"
        ]
    },
)
