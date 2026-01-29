import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

os.chdir(here)

with open(
    os.path.join(here, 'README.md'), encoding='utf-8'
) as readme_file:
    readme = readme_file.read()

version_contents = {}
with open(
    os.path.join(here, 'depoc', '_version.py'),
    encoding='utf-8'
) as f:
    exec(f.read(), version_contents)

setup(
    name='depoc',
    version=version_contents['VERSION'], 
    description='Python bindings for the Depoc API',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Hugo Belém',
    url='https://github.com/hugobelem/depoc-api',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'requests >= 2.32.3',
        'click  >= 8.1.8',
        'appdirs >= 1.4.4',
        'rich >= 13.9.4', 
    ],
    entry_points={
        'console_scripts': [
            'depoc = depoc.cli:main',
        ],
    },
    python_requires='>=3.12',
    setup_requires=['wheel'],
) 
