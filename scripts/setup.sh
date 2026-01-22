#!/bin/sh
./scripts/build-dropbear.sh
docker build containers/14.04-buildenv/ -t easylkb-1404buildenv
docker build containers/18.04-buildenv/ -t easylkb-1804buildenv
docker build containers/22.04-buildenv/ -t easylkb-2204buildenv
