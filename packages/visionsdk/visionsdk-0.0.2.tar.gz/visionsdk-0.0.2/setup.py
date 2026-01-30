import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="visionsdk",
    version="0.0.2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="visionsdk",
    author_email="sdk@neurarank.tech",
    license="MIT",
    packages=setuptools.find_packages(include=["visionsdk*"], exclude=["example"]),
    include_package_data=True,
)
