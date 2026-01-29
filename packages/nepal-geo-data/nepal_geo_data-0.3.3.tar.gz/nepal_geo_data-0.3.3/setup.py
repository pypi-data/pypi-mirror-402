import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nepal-geo-data",
    version="0.3.3",
    author="Bedbyas Pokhrel",
    author_email="bedbyaspokhrel@gmail.com",
    description="Comprehensive Python package offering Nepal's geographical data including GeoJSON for all 77 districts and 7 provinces.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bedbyaspokhrel/nepal-geo-data",
    project_urls={
        "Bug Tracker": "https://github.com/bedbyaspokhrel/nepal-geo-data/issues",
    },
    keywords="nepal geojson gis nepal-map districts provinces nepal-geography kathmandu data-visualization python-nepal",
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
