import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nepal-geo-data",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package providing geographical data for Nepal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nepal-geo-data",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/nepal-geo-data/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "nepal_geo_data": ["data/*.geojson"],
    },
)
