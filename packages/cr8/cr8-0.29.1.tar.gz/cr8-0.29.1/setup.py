#!/usr/bin/env python

from setuptools import setup

try:
    with open('README.rst', 'r', encoding='utf-8') as f:
        readme = f.read()
except IOError:
    readme = ''


setup(
    name='cr8',
    author='Mathias Fußenegger',
    author_email='pip@zignar.net',
    url='https://codeberg.org/mfussenegger/cr8',
    description='A collection of command line tools for crate devs',
    long_description=readme,
    long_description_content_type='text/x-rst',
    entry_points={
        'console_scripts': [
            'cr8 = cr8.__main__:main',
        ]
    },
    packages=['cr8'],
    package_data={
        "cr8": ["py.typed"]
    },
    install_requires=[
        'argh',
        'tqdm',
        'Faker>=4.0,<5.0',
        'aiohttp>=3.3,<4',
        'asyncpg'
    ],
    extras_require={
        'extra': ['uvloop>=0.18', 'pysimdjson'],
        "dev": ["asyncpg-stubs", "mypy"]
    },
    python_requires='>=3.11',
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm']
)
