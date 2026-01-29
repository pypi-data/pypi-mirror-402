import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyPhasesRecordloaderAlice",
    version="v0.2.0"[1:],
    author="Franz Ehrlich",
    author_email="fehrlichd@gmail.com",
    description="Adds a record loaders to the pyPhases package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/tud.ibmt.public/pyphases/pyphasesrecordloader/",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={"pyPhasesRecordloaderAlice": ["**/*.yaml"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pyPhases", "pyPhasesRecordloader", "pyedflib", "SleepHarmonizer"],
    python_requires=">=3.5",
)
