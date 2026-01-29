from setuptools import setup, find_packages

setup(
    name="gromacs-mdkit",
    version="1.0.3",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["rich>=13.0.0", "periodictable>=1.6.0"],
    entry_points={
        "console_scripts": [
            "mdkit=gromacs_mdkit.cli:main",
            "gromacs-mdkit=gromacs_mdkit.cli:main",
        ],
    },
)