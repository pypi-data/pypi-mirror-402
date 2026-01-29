from setuptools import setup, find_packages

setup(
    name="gitmatex",
    version="0.1.0",
    author="Your Name",
    author_email="youremail@gmail.com",
    description="A simple GitHub helper CLI tool",
    packages=find_packages(),
    py_modules=["gitmate"],
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "gitmate=gitmate:cli",
        ],
    },
    python_requires=">=3.7",
)
