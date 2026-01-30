from setuptools import setup, find_packages

setup(
    name="altasigma",
    version="3.10.4",
    author="AltaSigma GmbH",
    author_email="pypi@altasigma.com",
    packages=find_packages(exclude=['altasigma.test', 'altasigma.test.*']),
    url="https://www.altasigma.com",
    license="Proprietary",
    description="Python helpers for data science and ML workflows on the AltaSigma AI platform",
    long_description=open("README_pypi.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    classifiers=[
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    # Broadest possible ranges
    install_requires=[
        # Seems stable enough that a 3 release would probably affect us
        "requests>=2,<3",
        # 2 also works and seems to have not changed anything relevant for our use since 1. For that reason we won't limit it to <3, hoping nothing will change again
        # We are also currently developing against 2 (see the pinned requirements), so support for <2 may worsen if we are not careful. We should check when we can drop it.
        "pandas>=1",
        "ipython>=8",
        # Lowest version that classifies as python 3.10
        "boto3>=1.18.49,<2"
    ],
)
