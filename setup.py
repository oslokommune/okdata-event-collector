import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="okdata-event-collector",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="Code for putting data on a data stream",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oslokommune/okdata-event-collector/",
    packages=setuptools.find_packages(),
    install_requires=[
        "boto3",
        "aws-xray-sdk",
        "requests",
        "jsonschema",
        "python-keycloak",
        "okdata-aws",
        "okdata-resource-auth",
        "okdata-sdk >= 0.9.0",
    ],
)
