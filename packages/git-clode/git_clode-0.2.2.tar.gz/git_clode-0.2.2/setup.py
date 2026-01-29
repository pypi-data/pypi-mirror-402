from setuptools import setup

setup(
    name="git-clode",
    description="CLI tool to open git repositories quickly",
    author="Oli",
    author_email="oli@olillin.com",
    license="MIT",
    install_requires=[
        "colorama",
        "inquirer",
    ],
    entry_points={
        "console_scripts": [
            "clode=clode:main",
        ]
    },
)
