#!/usr/bin/env python
"""Setup script for tc-queue-system package."""

from setuptools import setup, find_packages
from pathlib import Path

readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''

version = '1.0.0'

setup(
    name='tc-queue-system',
    version=version,
    author='Yashvanth D',
    author_email='dev@taskcircuit.com',
    description='A simple message queue system with SQLite backend and Flask API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/task-circuit/tc-queue-system',
    project_urls={
        'Bug Tracker': 'https://github.com/task-circuit/tc-queue-system/issues',
        'Documentation': 'https://github.com/task-circuit/tc-queue-system#readme',
        'Source Code': 'https://github.com/task-circuit/tc-queue-system',
    },
    license='MIT',
    packages=find_packages(include=['tc_queue_system', 'tc_queue_system.*']),
    python_requires='>=3.8',
    install_requires=[],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'server': [
            'flask>=2.0.0',
        ],
        'all': [
            'flask>=2.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'tc-queue=tc_queue_system.service:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
    ],
    keywords='queue message-queue task-queue sqlite flask-api',
)

