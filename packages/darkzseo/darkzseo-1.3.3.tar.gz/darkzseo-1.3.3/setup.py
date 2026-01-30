from setuptools import setup
import os

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='darkzseo',
    version='1.3.3',
    description='DarkzSEO - Zero-Config 2026 Search Standard Auditor (CLI + HTML)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='DarkzSEO',
    url='https://github.com/yourusername/darkzseo',  # Update this
    py_modules=['darkzseo'],
    install_requires=[
        'beautifulsoup4>=4.12.0',
        'colorama>=0.4.6',
    ],
    entry_points={
        'console_scripts': [
            'darkzseo=darkzseo:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.7',
)
