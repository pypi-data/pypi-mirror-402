from __future__ import print_function
from setuptools import setup, find_packages
import sys
filepath = 'README.md'

setup(
    name="openquantum",
    version="0.0.4",
    author="J2hu",  #作者名字
    author_email="",
    description="New-Generation Architecture: Integrating AI (LLMs) and Quantum Computing. ",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    license="GNU General Public License v3 (GPLv3)",
    url="",  #github地址或其他地址
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
            'numpy>=1.14.0',   #所需要包的版本号
            'pyscf>=0.0.0',
            'pytorch>=2.0.0',
            'transformers>=4.0.0',
            'trl>=0.0.0',
            'braket>=0.0.0',
            'openqasm>=0.0.0',
    ],
    python_requires=">=3.9",
)
