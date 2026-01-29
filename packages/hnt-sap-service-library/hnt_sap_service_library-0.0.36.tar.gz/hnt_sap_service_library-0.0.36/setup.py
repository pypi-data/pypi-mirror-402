from setuptools import setup, find_packages

setup(name='hnt_sap_service_library',
    version='0.0.36',
    license='MIT License',
    author='Pepe',
    maintainer='Guillerme',
    keywords='nota_fiscal',
    description=u'Lib to access sap gui to run service transactions.',
    packages=find_packages(),
    package_data={'hnt_sap_gui': ['common/*', 'nota_fiscal/*']},
    install_requires=[
    'python-dotenv',
    'robotframework-sapguilibrary',
    ])