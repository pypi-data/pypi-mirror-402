from setuptools import setup, find_packages

setup(
    name="Topsis-RaghavPahwa-102303608",
    version="1.0.1",
    author="Raghav Pahwa",
    author_email="rpahwa_be23@thapar.edu",
    description="A command-line implementation of TOPSIS",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    license="MIT",
    entry_points={
        "console_scripts": [
            "topsis=topsis_raghavpahwa_102303608.topsis:main",
        ]
    },
    install_requires=["pandas", "numpy"],
    python_requires=">=3.7",
)
