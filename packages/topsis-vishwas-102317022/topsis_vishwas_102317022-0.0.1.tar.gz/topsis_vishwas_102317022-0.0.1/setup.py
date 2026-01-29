from setuptools import setup, find_packages

setup(
    name="topsis-vishwas-102317022",
    version="0.0.1",
    author="Vishwas",
    author_email="vvishwas_be23@thapar.edu",
    description="TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) Python package",
    
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    packages=find_packages(),

    install_requires=[
        "pandas",
        "numpy"
    ],

    entry_points={
        "console_scripts": [
            "topsis=topsis_vishwas_102317022.topsis:main"
        ]
    },

    python_requires=">=3.6",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
