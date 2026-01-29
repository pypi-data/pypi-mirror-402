from setuptools import setup, find_packages

setup(
    name="topsis-isha-102303007",
    version="1.0.0",
    author="Isha Gupta",
    author_email="igupta1_be23@thapar.edu",
    description="A Python package implementing TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    long_description=open("README.md").read() if __name__ != "__main__" else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_isha.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
