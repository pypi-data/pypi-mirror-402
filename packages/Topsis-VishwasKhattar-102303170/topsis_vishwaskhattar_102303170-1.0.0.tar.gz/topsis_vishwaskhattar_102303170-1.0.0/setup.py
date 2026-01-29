from setuptools import setup, find_packages

setup(
    name="Topsis-VishwasKhattar-102303170",
    version="1.0.0",
    author="Vishwas Khattar",
    author_email="your_email@gmail.com",
    description="A command-line implementation of TOPSIS",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vishwas_102303170.topsis:run"
        ]
    },
)
