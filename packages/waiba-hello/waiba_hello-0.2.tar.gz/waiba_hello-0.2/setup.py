from setuptools import setup, find_packages


with open("README.md", "r") as f:
    project_description = f.read()


setup(
    name="waiba_hello",
    version="0.2",
    author="waiba",
    description="A simple hello package",
    long_description=project_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        # Dependencies here
    ],
    python_requireds=">=3.0",
    entry_points={
        "console_scripts": [
            "waiba-hello = waiba_hello:hello",
        ],
    }
)