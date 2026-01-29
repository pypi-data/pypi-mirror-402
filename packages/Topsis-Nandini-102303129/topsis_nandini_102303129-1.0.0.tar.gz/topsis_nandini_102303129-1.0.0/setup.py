from setuptools import setup, find_packages

setup(
    name="Topsis-Nandini-102303129",
    version="1.0.0",
    author="Nandini Kumari",
    author_email="nkumari_be23@thapar.edu",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_nandini_102303129.topsis:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)