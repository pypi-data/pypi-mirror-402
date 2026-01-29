import os
from setuptools import setup


path = os.path.dirname(__file__)
with open(path + '/README.md', 'r', encoding='utf-8') as readme:
    long_description = readme.read()

with open(path + '/PocketTRC20/config.py', 'r') as config:
    contents = config.read()
result = contents.split()
__version__ = result[2][1:-1]

setup(
    name="PocketTRC20",
    version=__version__,
    description='Python TRON Blockchain Explorer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lao',
    url='https://github.com/codelao/PocketTRC20',
    license='MIT',
    install_requires=[
        'requests>=2.28.2', 'colorama>=0.4.6', 'progress>=1.6'
    ],
    packages=[
        'PocketTRC20'
    ],
    entry_points={
        'console_scripts': [
            'ptrc20=PocketTRC20.__main__:entry_point'
        ]
    }
)
