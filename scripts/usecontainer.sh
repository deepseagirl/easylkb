#!/bin/sh
CONTAINER=$1
shift 1
docker run -v `pwd`:/build -u $UID:$GID -ti $CONTAINER $@
