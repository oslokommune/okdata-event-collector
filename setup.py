import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="event-collectorr",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="Code for putting data on a data stream",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.oslo.kommune.no/origo-dataplatform/event-collector",
    packages=setuptools.find_packages(),
    install_requires=[
        'jsonschema==2.6.0',
        'requests==2.21.0'
    ]
)