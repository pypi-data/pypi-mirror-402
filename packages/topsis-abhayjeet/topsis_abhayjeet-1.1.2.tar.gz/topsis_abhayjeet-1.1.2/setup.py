from setuptools import setup, find_packages

setup(
    name="topsis-abhayjeet",
    version="1.1.2",
    author="Abhayjeet",
    url="https://pypi.org/project/topsis-abhayjeet/",
    author_email="abhayjeet5465@gmail.com",
    description="Implementation of TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_abhayjeet.topsis:main"
        ]
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
