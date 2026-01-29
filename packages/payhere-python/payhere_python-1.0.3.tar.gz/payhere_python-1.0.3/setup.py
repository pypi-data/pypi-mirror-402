from pathlib import Path

from setuptools import setup

PROJECT_ROOT = Path(__file__).parent

# Read README.md for the long description
readme_path = PROJECT_ROOT / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    # --- Core metadata (from pyproject.toml [project]) ---
    name="payhere-python",
    version="1.0.3",
    description="Unofficial Python SDK for PayHere Payment Gateway",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kavindu Harshitha",
    author_email="kavindu@apexkv.com",
    license="GPL-3.0-only",
    keywords=["payhere", "payment", "sdk", "sri-lanka", "python"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",

    # --- Dependencies (from pyproject.toml [project.dependencies]) ---
    install_requires=[
        "requests",
        "pydantic",
    ],

    # --- Package configuration ---
    # Treat the current directory as the `payhere_python` package so that
    # installations provide `import payhere_python`.
    packages=["payhere_python"],
    package_dir={"payhere_python": "."},

    # --- URLs (from pyproject.toml [project.urls]) ---
    project_urls={
        "Homepage": "https://github.com/apexkv/payhere-python",
        "Repository": "https://github.com/apexkv/payhere-python",
        "Issues": "https://github.com/apexkv/payhere-python/issues",
    },
)
