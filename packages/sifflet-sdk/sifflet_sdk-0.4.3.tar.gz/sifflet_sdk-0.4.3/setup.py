import setuptools
import sifflet_sdk

long_description = open("README.md", "r", encoding="utf-8").read()
requirements = [i.strip() for i in open("requirements.txt").readlines()]

setuptools.setup(
    name="sifflet_sdk",
    version=sifflet_sdk.__version__,
    author="Sifflet",
    author_email="support@siffletdata.com",
    url="https://www.siffletdata.com/",
    description="Sifflet sdk",
    py_modules=["sifflet_sdk"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    packages=setuptools.find_packages(include=["sifflet_sdk", "sifflet_sdk.*"]),
    python_requires=">=3.7",
    install_requires=requirements,
)
