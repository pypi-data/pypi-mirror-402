from setuptools import setup, find_packages

setup(
    name='pycsio',
    version='0.1.6',
    packages=find_packages(),
    install_requires=[
        "tqdm",
        "numba",
        "numpy",
        "rich",
        "imagehash",
        "pillow",
        "pycryptodome"
    ],
    author='admin',
    author_email='admin@email.com',
    description='My useful Tools',
    url='https://github.com/admin',
)