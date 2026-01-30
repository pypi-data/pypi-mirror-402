'''
    breve descripcion del paquete
'''

from setuptools import setup, find_packages

setup(
    name='gss-bi-udfs',
    version='0.1.1',
    author='Geronimo Forconi',
    description='Utilidades reutilizables para Spark y Delta Lake en arquitecturas Lakehouse.',
    packages=find_packages(),
    install_requires=['pyspark>=3.0.0'],
)