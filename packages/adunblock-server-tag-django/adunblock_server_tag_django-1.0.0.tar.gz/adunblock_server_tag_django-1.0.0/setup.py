from setuptools import setup, find_packages

setup(
    name='adunblock-server-tag-django',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    license='ISC',
    description='A Django package to fetch and render scripts from a remote URL.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'Django',
        'requests',
    ],
)
