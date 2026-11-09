#!/bin/sh
set -eu
mkdir -p /data
chown -R hawkeye:hawkeye /data
exec gosu hawkeye "$@"
