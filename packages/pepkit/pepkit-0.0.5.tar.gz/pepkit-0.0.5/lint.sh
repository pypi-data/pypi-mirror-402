#!/bin/bash

flake8 . --count --max-complexity=11 --max-line-length=90 \
	--per-file-ignores="test.py:F401, clustering.py:C901, filter.py:C901, sequence.py:C901" \
	--exclude venv,__init__.py,rmsd.py\
	--statistics