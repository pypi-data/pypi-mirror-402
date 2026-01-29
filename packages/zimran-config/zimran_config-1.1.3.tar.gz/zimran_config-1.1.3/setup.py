from os import environ

from setuptools import find_namespace_packages, setup

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='zimran-config',
    version=environ['GITHUB_REF_NAME'],
    description='Pydantic based configuration for FastAPI services',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_namespace_packages(include=['zimran.*']),
    install_requires=['pydantic-settings==2.*'],
    python_requires='>=3.10',
    zip_file=False,
    entry_points={
        'console_scripts': [
            'zimran-sync-api-docs=zimran.cli.sync_api_docs:main',
        ],
    },
)
