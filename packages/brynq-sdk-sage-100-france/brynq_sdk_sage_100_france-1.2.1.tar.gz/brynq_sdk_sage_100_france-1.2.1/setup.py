from setuptools import setup, find_namespace_packages

setup(
    name='brynq_sdk_sage_100_france',
    version='1.2.1',
    description='Sage 100 France wrapper from BrynQ',
    long_description='Sage 100 France wrapper from BrynQ',
    author='BrynQ',
    author_email='support@brynq.com',
    packages=find_namespace_packages(include=['brynq_sdk*']),
    license='BrynQ License',
    install_requires=[
        'brynq-sdk-brynq>=4,<5',
    ],
    zip_safe=False,
)
