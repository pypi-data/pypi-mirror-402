from setuptools import setup

setup(
    name="weatherutilv1",
    version="0.1.0",
    author="Jarek Smith",
    author_email="jarek.smith.88@gmail.com",
    packages=["weatherutil"],
    python_requires=">=3.12.4, <4",
    description="A sample package containing basic data stat methods",
    long_description=open("README.md").read(),
)
