import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="reldi-tokeniser",
    version="1.0.1",
    author="Zavod za lingvistiku Filozofskog fakulteta Sveučilišta u Zagrebu",
    author_email="zzl-admin@ffzg.hr",
    description="Tokeniser and sentence splitter for Croatian.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zzl-ffzg/reldi-tokeniser",
    packages=['reldi_hr_tokeniser'],
    package_dir={'reldi_hr_tokeniser': 'reldi_hr_tokeniser'},
    package_data={'reldi_hr_tokeniser': ['data/reldi_hr_tokeniser/hr.abbrev']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
