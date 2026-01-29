from setuptools import setup, find_packages
import os

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = f"{lib_folder}/requirements.txt"
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()

setup(
    name="pyninaapiio",
    packages=find_packages(),
    version="0.2.2.13.7",
    license="MIT",
    description="Python Wrapper for N.I.N.A. Advanced API",
    long_description=" ".join(
        [
            "Lightweight Python 3 module to receive data via",
            "API from N.I.N.A. Advanced API.",
        ],
    ),
    author="Markus Winkler",
    author_email="winkler.info@icloud.com",
    url="https://github.com/mawinkler/pyninaapiio",
    keywords=["N.I.N.A.", "NinaAPI", "Python"],
    install_requires=install_requires,
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
