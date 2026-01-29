from setuptools import setup, find_packages

setup(
    name="topsis-aadi-102303612",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_aadi_102303612.topsis:main"
        ]
    },
    author="Aadi",
    description="TOPSIS implementation",
)
