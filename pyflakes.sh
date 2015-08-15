#!/bin/bash

echo "============================================================"
echo "== pyflakes =="
pyflakes flowr | grep -v migration
