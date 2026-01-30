from setuptools import setup, find_packages

setup(
    name='fleetmqsdk',
    version='0.0.19',
    description='A convenient SDK for FleetMQ',
    author='Nicole',
    author_email='nicole@fleetmq.io',
    packages=find_packages(),
    install_requires=[
        'google-api-python-client',
        'pyzmq',
        'setuptools'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
