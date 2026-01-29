#! /usr/bin/env bash
set -e
set -x

python aptrade/tests_pre_start.py

bash scripts/test.sh "$@"
