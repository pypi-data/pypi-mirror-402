from setuptools import setup, find_packages

setup(
    name="Topsis-Gurshaan-Bajwa-102303264",
    version="0.0.3",
    author="Gurshaan Bajwa",
    author_email="gbajwa_be23@thapar.edu",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_gurshaan_bajwa_102303264.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
