from setuptools import setup, find_packages

setup(
    name="dab_py",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "matplotlib"
    ],
    license="AGPL-3.0",
    author="Alun Sagara Putra (CNR Internship)",
    description="A Python client for DAB Terms API and DAB API (WHOS / HIS-Central API)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ESSI-Lab/dab-py/tree/main",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    include_package_data=True,
)
