from setuptools import setup, find_packages


setup(
    name='dianpy',
    description='DianPy a special parser for working with the dian scoreboard',
    version='1.0.4',
    install_requires=[
        'pydantic-xml>=2.18.0',
        'lxml>=6.0.2'
    ],
    packages=find_packages()
)
