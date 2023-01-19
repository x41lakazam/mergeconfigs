from setuptools import setup

try:
    long_description = open("README.md").read()
except:
    long_description = ""


setup(
    name='mergeconfigs',
    version='0.2',
    description='Help developers with config files',
    long_description=long_description,
    url="https://github.com/x41lakazam/mergeconfigs",
    author='Eyal Chocron',
    maintainer="Eyal Chocron",
    author_email='x41lakazam@gmail.com',
    maintainer_email='x41lakazam@gmail.com',
    keywords=["config", "yaml", "inheritance", "templates"],
    packages=['mergeconfigs'],
    install_requires=[
        'click',
    ],
    )
