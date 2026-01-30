#!/usr/bin/env python3
"""IAED: Introduction to algorithms and data structures
search: linear and binary
sorting: selection, insertion, bubble, shell, quick, merge, heap, counting, radix LSB/MSB and priority queues
hash-tables: external, linear probing, double hashing
tree: binary search, AVL
graph: breadth transversal, depth transversal
"""

import setuptools

with open("README.md", encoding="utf8") as fh:
    readme = fh.read()

setuptools.setup(name='iaed',
	version='1.0.4', # 1.0.3 test
	author='Pedro Reis dos Santos',
	author_email="reis.santos@tecnico.ulisboa.pt",
	description="IAED: Introduction to algorithms and data structures",
	long_description=readme,
	long_description_content_type="text/x-rst",
	license = 'MIT',
	url="https://github.com/pedroreissantos/iaed",
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		'Intended Audience :: Developers',
		'Topic :: Software Development :: Build Tools',
		'Development Status :: 4 - Beta',
		'Environment :: Console',
	],
	python_requires='>=3.6',
	py_modules = ['iaed'],
	packages=setuptools.find_packages(),
)
