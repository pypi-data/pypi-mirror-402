from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Topsis-Harsaihaj-123456",
    version="1.0.6",
    author="Harsaihaj Singh",
    author_email="harsaihaj@example.com",
    description="TOPSIS package for Multi-Criteria Decision Making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    py_modules=["topsis"],
    entry_points={
        "console_scripts": [
            "topsis=topsis:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
