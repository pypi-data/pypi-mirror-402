#!/bin/sh
python -m pip install --upgrade pip build setuptools wheel setuptools-scm
python -m build --wheel --no-isolation --outdir dist/
rm -rf ./build
