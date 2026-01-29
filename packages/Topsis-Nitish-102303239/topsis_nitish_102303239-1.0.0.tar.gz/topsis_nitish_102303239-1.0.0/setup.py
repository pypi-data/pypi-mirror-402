from setuptools import setup, find_packages

setup(
    name="Topsis-Nitish-102303239",
    version="1.0.0",
    author="Nitish",
    author_email="nitish@example.com",
    description="A Python package for implementing TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis-nitish=topsis_nitish_102303239.topsis:main",
        ]
    },
)
