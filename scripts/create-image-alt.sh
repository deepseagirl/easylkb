#!/bin/bash
# rootfs for old kernels
set -e

# Configuration
IMG_SIZE=50  # Size in MB
IMG_NAME="initramfs.img"
WORK_DIR="initramfs_build"

# Clean up any previous build
rm -rf $WORK_DIR
mkdir -p $WORK_DIR
cd $WORK_DIR

# Create directory structure
mkdir -p {bin,sbin,etc,proc,sys,dev,usr,root}

# Download static busybox
echo "Downloading busybox..."
wget -q https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox
chmod +x busybox
mv busybox bin/

echo "Creating symlinks for all busybox commands..."
cd bin
for cmd in $(./busybox --list); do
    ln -s busybox "$cmd"
done
cd ..

# install our prebuilt copy of dropbear
mkdir -p usr/bin
cp ../dropbearmulti usr/bin
cd usr/bin
ln -s dropbearmulti dropbear
ln -s dropbearmulti dbclient
ln -s dropbearmulti dropbearkey
ln -s dropbearmulti dropbearconvert
ln -s dropbearmulti scp
cd ../..

mkdir -p etc/dropbear
ssh-keygen -f ../rootfs.id_rsa -t rsa -N ''
mkdir -p root/.ssh
cat ../rootfs.id_rsa.pub >> root/.ssh/authorized_keys
chmod 0600 root/.ssh/authorized_keys
chmod 0700 root/.ssh/
chmod 0700 root/

# Create inittab for busybox init
cat > etc/inittab << 'EOF'
::sysinit:/etc/init.d/rcS
::ctrlaltdel:/sbin/reboot
ttyS0::respawn:/bin/sh -l
::shutdown:/bin/umount -a -r
EOF

# create a user so we can use dropbear
cat > etc/passwd << 'EOF'
root:x:0:0:root:/root:/bin/sh
EOF

cat > etc/group << 'EOF'
root:x:0:
EOF

# Create startup script with tmpfs and networking
mkdir -p etc/init.d
cat > etc/init.d/rcS << 'EOF'
#!/bin/sh

mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts
mount -o remount,rw /

# Mount tmpfs
mount -t tmpfs none /tmp
mount -t tmpfs none /run
mkdir -p /run/lock
mkdir -p /var/lock

# Setup networking
ip link set lo up

# If you have eth0 (QEMU with -netdev)
if ip link show eth0 2>/dev/null; then
    ip link set eth0 up
    # Use DHCP if available
    if command -v udhcpc >/dev/null; then
        udhcpc -i eth0 -s /etc/udhcpc/simple.script
    else
        # Static IP fallback
        ip addr add 10.0.2.15/24 dev eth0
        ip route add default via 10.0.2.10
    fi
fi

hostname linux

echo "Busybox initramfs booted successfully"
echo "Network interfaces:"
ip addr show

dropbear -P /tmp/dropbear.pid -R
EOF
chmod +x etc/init.d/rcS

# Create simple udhcpc script for DHCP
mkdir -p etc/udhcpc
cat > etc/udhcpc/simple.script << 'EOF'
#!/bin/sh
case "$1" in
    bound|renew)
        ip addr add $ip/$mask dev $interface
        [ -n "$router" ] && ip route add default via $router
        [ -n "$domain" ] && echo "search $domain" > /etc/resolv.conf
        for dns in $dns; do
            echo "nameserver $dns" >> /etc/resolv.conf
        done
        ;;
    deconfig)
        ip addr flush dev $interface
        ;;
esac
EOF
chmod +x etc/udhcpc/simple.script

mkdir tmp

# Create the image file
cd ..
echo "Creating disk image..."
dd if=/dev/zero of=$IMG_NAME bs=1M count=$IMG_SIZE status=progress

# Format as ext4
echo "Formatting as ext4..."
mkfs.ext4 -O ^metadata_csum,^64bit -F $IMG_NAME

# Mount and populate
echo "Populating image..."
mkdir -p mnt
sudo mount -o loop $IMG_NAME mnt
sudo cp -a $WORK_DIR/* mnt/
sudo chown -R root mnt/
sudo chgrp -R root mnt/
sudo umount mnt
rmdir mnt

# Cleanup
rm -rf $WORK_DIR

mv $IMG_NAME rootfs.img
