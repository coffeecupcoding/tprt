import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tprt",
    version="0.9.3",
    author="James Hewitt",
    author_email="coffeecupcoding@caurinus.com",
    description="Provides a greylisting policy server for Postfix",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/coffeecupcoding/tprt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
)
