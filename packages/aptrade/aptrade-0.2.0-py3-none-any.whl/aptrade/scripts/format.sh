#!/bin/sh -e
set -x

ruff check aptrade scripts --fix
ruff format aptrade scripts
