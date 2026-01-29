import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="topsis-sharv-102303341",
    version="1.0.0",
    author="Sharv",
    author_email="sharv@example.com",
    description="A Python package for TOPSIS method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pandas",
        "topsispy",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_sharv_102303341.topsis:main",
        ],
    },
    python_requires='>=3.6',
)
