from setuptools import setup, find_packages

setup(
    name='IfritAI',                 # The package name
    version='2.1.4',                # Version number
    packages=find_packages(),       # Automatically discover all packages and subpackages
    description='AI modifiers for FF8 monsters',  # Short description
    author='hobbitdur',             # Author's name
    url='https://github.com/HobbitDur/IfritEnhanced',  # GitHub or project URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',        # Minimum Python version requirement
)