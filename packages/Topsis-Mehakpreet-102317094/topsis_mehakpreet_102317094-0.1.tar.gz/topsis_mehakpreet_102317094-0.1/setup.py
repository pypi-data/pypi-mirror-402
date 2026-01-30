from setuptools import setup

setup(
    name="Topsis-Mehakpreet-102317094",
    version="0.1",
    packages=["topsis_mehak"],
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_mehak.topsis:main"
        ]
    },
)
