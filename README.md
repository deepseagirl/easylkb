# easylkb - Easy Linux Kernel Builder 

easylkb is a simple script designed to make Linux Kernel Debugging easier and more accessible.

this project was originally released in tmp.0ut volume 3: https://tmpout.sh/3/20.html

this article is a good introduction to this tool: https://hackaday.com/2023/11/22/linux-fu-easy-kernel-debugging/

## How do you install easylkb?

easylkb is best run on a bare metal Linux system. You need the following things installed in order to use it:

- python3
- curl
- gcc
- make
- qemu
- debootstrap

Install all prerequisites on Debian/Ubuntu

```
sudo apt update
sudo apt install make gcc flex bison libncurses-dev libelf-dev libssl-dev debootstrap
```

You can clone this repo and run from the easylkb directory, or you can install with pip (not yet lol). 

```
pip install easylkb
```

## How do you use easylkb?

Build a specific mainline kernel version:

```
easylkb -k 6.2
```

Build some other kernel in a directory:
```
easylkb -p path/to/linux/
```

Command line flags are tied to specific parts of the build process.

To (d)ownload, (c)onfigure, and co(m)pile a kernel
```
easylkb -k 6.2 -dcm
```

To build a Debian (i)mage from this kernel
```
easylkb -k 6.2 -i
```

To (r)un the generated image:
```
easylkb -k 6.2 -r
```

Combine all of these steps into one:
```
easylkb -k 6.2 -a
```

When it's running, it will run qemu with the Debian image and expose ssh and GDB debugging features accessible via localhost.

## How Do I Interact With The Image?

The image, keys, and run script are stored in the img/ directory within the kernel source.

You can ssh into your image like so:
```
ssh root@localhost -p 10021 -i ~/kernel/linux-6.2/img/bullseye.id_rsa
```

The default login for the resulting image is the user "root" with no password.

This is an example ssh config entry for the resulting image, which you can add to your `~/.ssh/config` file.
```
Host linux62
  HostName localhost
  User root
  Port 10021
  IdentityFile ~/kernel/linux-6.2/img/bullseye.id_rsa
  StrictHostKeyChecking no
```

Now you can ssh into your kernel by doing:
```
ssh linux62
```

You can scp files by doing
```
scp myfile.bin linux62:
```

## Kernel Debugging

To debug the kernel, you need `$KERNEL_DIR/scripts/gdb/vmlinux-gdb.py`

Add this to your `~/.gdbinit` file if you want to debug this kernel, changing the path to the kernel source you're working with.
```
add-auto-load-safe-path /home/user/kernel/linux-6.2/scripts/gdb/vmlinux-gdb.py
```

Now to debug just do
```
cd /path/to/your/kernel/
gdb ./vmlinux
```
Once you're in gdb just do this:
```
(gdb) lx-symbols
(gdb) target remote :1234
```
Wow! You're debugging the kernel you just built, pretty neat.

For more info on kernel debugging with gdb:
- https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html

## Known Issues

because this is a generic tool, there may be some instances where the example kernel config doesn't work for your kernel version.

here are some documented fixes:
- https://github.com/deepseagirl/easylkb/issues/4 Add `DEBUG_INFO_DWARF5` to config for kernel version 6.8 or newer

