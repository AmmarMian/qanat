#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['rich', 'rich_click', 'SQLAlchemy',
                'GitPython', 'pyyaml', 'psutil',
                'simple-term-menu', 'art']

test_requirements = ['pytest>=3', 'flake8>=3.7.8',
                     'coverage>=4.5.4']

setup(
    author="Ammar Mian",
    author_email='ammar.mian@univ-smb.fr',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    description="Minimal package to manage and reproduce research experiments.",
    entry_points={
        'console_scripts': [
            'qanat=qanat.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='qanat',
    name='qanat',
    packages=find_packages(include=['qanat', 'qanat.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ammarmian/qanat',
    version='0.1.0',
    zip_safe=False,
)
