import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = {}
with open("src/simple_error_log/__info__.py") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="simple_error_log",
    version=version["__package_version__"],
    author="D Iberson-Hurst",
    author_email="",
    description="A python package containing classes for logging errors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[],
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    tests_require=["pytest", "pytest-cov", "pytest-mock", "ruff"],
    python_requires=">=3.10",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
