import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mockupfle",
    version="0.0.1",
    author="A. Jesse Jiryu Davis",
    author_email="jesse@mongodb.com",
    description="Mock mongo-fle daemon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mongodb-labs/mockupfle",
    packages=setuptools.find_packages(),
    install_requires=['mockupdb', 'pymongo', 'python-daemon'],
    entry_points={
        'console_scripts': ['mockupfle=mockupfle:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
