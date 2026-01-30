from setuptools import setup, find_packages

setup(
    name="secureproximity",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "bleak>=0.21.0"
    ],
    entry_points={
        "console_scripts": [
            "secure-proximity=secureproximity.cli:main",
        ],
    },
    author="Nishant Gaurav",
    author_email="codewithevilxd@gmail.com",
    description="Advanced security CLI tool that locks your system when your phone moves out of Bluetooth range.",
    long_description=open("README.md", encoding="utf-8").read() if True else "",
    long_description_content_type="text/markdown",
    url="https://github.com/codewithevilxd/SecureProximity",
    python_requires=">=3.8",
)
