from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Topsis-Suhani-102313038",
    version="1.0.1",
    author="Suhani Gupta",
    author_email="suhani.work04@gmail.com",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis-suhani=topsis_.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
)