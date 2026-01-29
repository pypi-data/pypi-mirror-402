import setuptools
import sifflet_cli

long_description = open("README.md", "r", encoding="utf-8").read()
requirements = [i.strip() for i in open("requirements.txt").readlines()]

setuptools.setup(
    name="sifflet",
    version=sifflet_cli.__version__,
    author="Sifflet",
    author_email="support@siffletdata.com",
    url="https://www.siffletdata.com/",
    description="Sifflet CLI",
    py_modules=["sifflet_cli"],
    entry_points={
        "console_scripts": [
            "sifflet = sifflet_cli.cli:main",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    packages=setuptools.find_packages(include=["sifflet_cli", "sifflet_cli.*"]),
    python_requires=">=3.7",
    install_requires=requirements,
)
