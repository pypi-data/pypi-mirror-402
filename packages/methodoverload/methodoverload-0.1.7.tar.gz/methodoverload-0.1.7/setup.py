from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="methodoverload",
    version="0.1.7",
    author="Mohd Arbaaz Siddiqui",
    author_email="arbaazcode@gmail.com",
    description="Python method and function overloading library with type hint resolution.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mohdcodes/pyoverload",
    packages=find_packages(),
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    include_package_data=True,
    install_requires=[],
    project_urls={
        "Homepage": "https://github.com/mohdcodes/pyoverload",
        "Repository": "https://github.com/mohdcodes/pyoverload.git",
        "Documentation": "https://github.com/mohdcodes/pyoverload/tree/main/methodoverload/docs",
        "Changelog": "https://github.com/mohdcodes/pyoverload/releases",
        "Issues": "https://github.com/mohdcodes/pyoverload/tree/main/methodoverload/issues",
        "Features": "https://github.com/mohdcodes/pyoverload/tree/main/methodoverload/features",
    },
)


