from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cleantam",
    version="0.1.1",
    author="Federico Gabriel Gutierrez",
    author_email="gutierrezfedericog@gmail.com",
    description="Una extensión de Pandas para limpiar datos con formato latinoamericano",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fedco-gtz/cleantam",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "pandas",
    ],
)