from setuptools import setup, find_packages

setup(
    name="topsis-tanishka-102303245",
    version="1.0.0",
    author="Tanishka",
    author_email="tanishkarathee2705@gmail.com",
    description="TOPSIS implementation for multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
    python_requires=">=3.6",
)
