from setuptools import setup, find_packages

setup(
    name="Topsis-Divye-ROLLNUMBER",
    version="1.0.1",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_divye_rollnumber.topsis:main"
        ]
    },
)


