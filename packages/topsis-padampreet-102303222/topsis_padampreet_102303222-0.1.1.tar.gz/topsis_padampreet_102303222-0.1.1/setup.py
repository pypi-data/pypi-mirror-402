from setuptools import setup, find_packages

setup(
    name="topsis_padampreet_102303222",
    version="0.1.1",
    author="Padampreet Singh",
    author_email="spadampreet@gmail.com",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_padampreet_102303222.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
