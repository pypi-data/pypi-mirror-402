from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gromacs-mdkit",
    version="1.0.0",
    author="Pengcheng Li",
    author_email="your-email@example.com",
    description="A molecular dynamics preprocessing toolkit for GROMACS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gromacs-mdkit",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "rich>=13.0.0",
        "periodictable>=1.6.0",
    ],
    entry_points={
        "console_scripts": [
            "gromacs-mdkit=gromacs_mdkit.gromacs:main",
            "mdkit=gromacs_mdkit.gromacs:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Intended Audience :: Science/Research",
    ],
    python_requires=">=3.8",
)