from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cashy",
    version="1.0.0",
    author="Mohsin Nasir", 
    author_email="mohsinnasirdps@gmail.com",
    description="A simple Live currency converter using the Frankfurter API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mohsin-nasir/cashy",
    packages=["cashy"],
    package_dir={"cashy": "."},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.0.0",
    ],
)
