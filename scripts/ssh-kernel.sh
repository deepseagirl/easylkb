#!/bin/sh
ssh root@localhost -p 10021 -i ./kernel/linux-$1/img/rootfs.id_rsa -o "UserKnownHostsFile=/dev/null"
