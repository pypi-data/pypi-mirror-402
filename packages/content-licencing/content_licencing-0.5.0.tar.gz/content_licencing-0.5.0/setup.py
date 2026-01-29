from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

install_requires = []

setup(
    name='content_licencing',
    version='0.5.0',
    description='Content licencing for django',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='The MIT License',
    platforms=['OS Independent'],
    keywords='django, licence',
    author='Thomas Uher',
    author_email='thomas.uher@sisol-systems.com',
    url='https://github.com/SiSol-Systems/content-licencing',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    include_package_data=True,
    install_requires=install_requires,
)
