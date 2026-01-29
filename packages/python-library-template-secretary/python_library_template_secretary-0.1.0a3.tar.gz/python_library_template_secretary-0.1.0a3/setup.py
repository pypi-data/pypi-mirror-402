# this is the setup.py file for the project
from setuptools import setup, find_packages

setup(
    name='python_library_template_secretary',
    version='0.1.0a3',
    packages=find_packages(),
    install_requires=[
        
    ],  # list your project dependencies here
    entry_points={
        'console_scripts': [
            'test_function=python_library_template_secretary:test_function',
        ],
    },
)