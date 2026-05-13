from setuptools import setup, find_packages

setup(
    name='BomScanner',
    version='1.0.0',
    description='Simple NVD scanner CLI',
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'bomscanner=bomscanner.cli:main',
        ],
    },
    install_requires=[],
)
