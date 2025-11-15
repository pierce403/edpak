from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="edpak-validator",
    version="1.0.0",
    author="Edpak Contributors",
    description="A tool for verifying edpak file compliance with the edpak standard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pierce403/edpak",
    py_modules=["edpak_validator"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "edpak-verify=edpak_validator:main",
        ],
    },
)
