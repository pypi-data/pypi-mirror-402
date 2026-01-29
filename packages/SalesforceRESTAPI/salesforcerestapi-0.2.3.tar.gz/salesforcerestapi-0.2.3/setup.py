from setuptools import setup, find_packages

setup(
    name='SalesforceRESTAPI',
    version='0.2.3',
    packages=find_packages(),
    install_requires=[],
    author='Pedro Bazan',
    author_email='pedro.bazan@arcsona.com',
    description='A simple library to interact with Salesforce REST API using OAuth 2.0 Client Credentials Flow.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/arcsona/SalesforceRESTAPI',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
