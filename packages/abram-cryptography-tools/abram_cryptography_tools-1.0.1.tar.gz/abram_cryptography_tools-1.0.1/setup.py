from setuptools import setup

setup(
    name="abram_cryptography_tools",
    version="1.0.1",
    description="A custom cryptography library that turns your text into a secret code",
    author="Abram Jindal",
    py_modules=["abram_cryptography"],
    install_requires=["rich"]
)