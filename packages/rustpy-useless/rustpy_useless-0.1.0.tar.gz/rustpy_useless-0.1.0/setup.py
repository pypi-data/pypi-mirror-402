from setuptools import setup, find_packages

setup(
    name="rustpy-useless",
    version="0.1.0",
    description="A Python library that parodies Rust with intentionally bad optimization",
    author="Klee",
    author_email="porfavornaotenhoemail@gmail.com",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
