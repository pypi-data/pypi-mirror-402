from setuptools import setup, find_packages

setup(
    name="topsis_mrinank_102303235",
    version="0.0.1",
    description="TOPSIS CLI tool",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Mrinank",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_mrinank_102303235.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires=">=3.8"
)
