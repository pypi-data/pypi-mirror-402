from setuptools import setup, find_packages


setup(
    name='little_json',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[],
    author='Jasurbek',
    author_email='olimjonovzilxa@gmail.com',
    description='Drawing operations and json',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    requires=['ujson'],
    python_requires='>=3.6'
)