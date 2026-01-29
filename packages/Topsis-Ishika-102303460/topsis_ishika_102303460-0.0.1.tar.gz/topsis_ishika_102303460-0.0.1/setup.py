from setuptools import setup, find_packages

setup(
    name="Topsis-Ishika-102303460",
    version="0.0.1",
    author="Ishika",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_ishika_102303460.topsis:main"
        ]
    },
)
