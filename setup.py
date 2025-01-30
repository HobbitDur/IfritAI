from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()
setup(
    name="IfritAI",
    version="1.0.0",
    author="HobbitDur",
    description="Powerful monster AI editor for FF8 .dat files",
    url="https://www.patreon.com/c/HobbitMods",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    install_requires=requirements,
    project_urls={
        "Donate": "https://www.patreon.com/c/HobbitMods",
    },
)