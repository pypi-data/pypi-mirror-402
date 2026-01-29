"""Setup file for the sphinxcontrib_rust extension"""

import subprocess
from pathlib import Path
from shutil import which

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

LONG_DESC = Path("index.rst").read_text(encoding="utf-8")

__VERSION__ = "1.0.1"
__THIS_DIR = Path(__file__).parent.absolute()
__CARGO = which("cargo")
if not __CARGO:
    raise ValueError("Could not find cargo executable on path")


# XXX: Use pip install -vvv -e to debug the build.
# pip install does not print the output from cargo otherwise


def run_cargo(command: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run subprocess to build the sphinx-rustdocgen crate"""
    command = [__CARGO, command, *args]
    return subprocess.run(
        command,
        check=True,
        text=True,
        cwd=f"{__THIS_DIR}/sphinx-rustdocgen",
    )


class CargoBuild(develop):
    """Command to install debug version of the sphinx-rustdocgen executable"""

    def run(self):
        run_cargo("install", "--debug", "--path", ".")
        develop.run(self)


class CargoInstall(install):
    """Command to install release version of the sphinx-rustdocgen executable"""

    def run(self):
        run_cargo("install", "--path", ".")
        install.run(self)


setup(
    name="sphinxcontrib-rust",
    version=__VERSION__,
    description="Sphinx extension for documenting Rust projects",
    long_description=LONG_DESC,
    long_description_content_type="text/plain",
    python_requires=">=3.9",
    install_requires=[
        "sphinx>=7,<9",
        "markdown-it-py>=3,<5",
        "myst-parser>=3,<5",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Sphinx :: Domain",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Rust",
        "Topic :: Documentation :: Sphinx",
    ],
    extras_require={
        "dev": [
            "black",
            "pylint",
            "pytest-cov",
            "sphinx_rtd_theme",
        ],
    },
    packages=find_packages(),
    package_data={"sphinxcontrib_rust": ["sphinx-rustdocgen/**"]},
    include_package_data=True,
    cmdclass={
        "develop": CargoBuild,
        "install": CargoInstall,
    },
    url="https://gitlab.com/munir0b0t/sphinxcontrib-rust",
    author="Munir Contractor",
    license="GPL-3.0-or-later",
)
