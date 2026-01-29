from setuptools import setup, find_packages

setup(
    name='Ramlal_STT',
    version='0.1',
    author='Ramlal',
    author_email='ramlal@gmail.com',
    description='This is speech to text package for Ramlal.'
)
__package__ = find_packages(),
install_requirment = [
    'selenium',
    'webdriver_manager'
]


