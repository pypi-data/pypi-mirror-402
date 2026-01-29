from setuptools import setup

setup(
    name="happycli",
    version="1.0.2",
    packages=["happycli"],  # force include
    entry_points={
        "console_scripts": [
            "happy = happycli.app:main"
        ]
    },
)
