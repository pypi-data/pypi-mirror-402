from pathlib import Path

from setuptools import find_packages, setup


HERE = Path(__file__).parent
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding="utf-8")


setup(
    name="daylily_carrier_tracking",
    version="0.1.0",
    description="Unified multi-carrier tracking (FedEx implemented; UPS/USPS pending)",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/Daylily-Informatics/daylily-carrier-tracking",
    license="MIT",
    license_files=["LICENSE"],
    python_requires=">=3.10",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    install_requires=[
        "requests",
        "yaml_config_day",
    ],
    entry_points={
        "console_scripts": [
            "tday=daylily_carrier_tracking.cli:main",
            "tracking_day=daylily_carrier_tracking.cli:main",  # deprecated alias
        ],
    },
)
