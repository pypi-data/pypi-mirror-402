from setuptools import setup

setup(
    name="topsis-yuvraj-102303119",
    version="1.0.4",
    packages=["topsis_yuvraj_102303119"],
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_yuvraj_102303119.topsis:run"
        ]
    },
)
