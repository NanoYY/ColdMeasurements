import setuptools

setuptools.setup(
    name = "nanodrivers",
    version = "0.0.3",
    author = "Ekaterina Mukhanova",
    author_email = "ekaterina.mukhanova@aalto.fi",
    description = "drivers for scientific microwave equipment",
    python_requires = ">=3.6",
    install_requires=[
            "nidaqmx",
        ])