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
        "aws-xray-sdk",
        "boto3",
        "jsonschema",
        "okdata-aws",
        "okdata-resource-auth>=0.1.3",
        "okdata-sdk >= 0.9.0",
        "python-keycloak",
        "requests>=2.26.0,<3.0.0",
        # We don't really need this, but AWS Lambda started including this
        # library in the Python 3.9 runtime, and `requests` will swap the
        # standard library `json` out for it when it's present in the
        # environment. Include it here explicitly so we are sure which JSON
        # library `requests` picks.
        #
        # TODO: Remove once `requests` 3.0.0 is out, since `simplejson` support
        # is dropped there.
        "simplejson",
    ],
)
