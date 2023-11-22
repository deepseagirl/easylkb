#!/usr/bin/env python3

import argparse
import subprocess
import re
import os
import sys

class Kbuilder:
    def __init__(self, KConfig=None, KPath=None, KVersion="", KHostname="localhost"):
        self.BaseDir = os.getcwd() + "/"
        self.LogDir = self.BaseDir + "log/"
        self.KVersion = KVersion # The kernel version
        if KConfig is not None:
            self.KConfig = KConfig
        else:
            self.KConfig="config/example.KConfig" # Default KConfig location
        if KPath is not None:
            self.KPath = KPath
        else:
            self.KPath = f"{self.BaseDir}kernel/linux-{KVersion}/" # Path to this kernel
        self.ImgPath = self.KPath + "img/"
        self.KHostname = KHostname
        self.isDownloaded = False # Is the tarball downloaded?
        self.isExtracted = False # Is the tarball extracted?
        self.nproc = int(subprocess.run(["nproc"], capture_output=True).stdout.decode("utf-8").split("\n")[0])
        self.runkPath = self.ImgPath + "runk.sh"
        self.runkScript =  "#!/usr/bin/env bash\n"
        self.runkScript += f"qemu-system-x86_64"
        self.runkScript += f" -m 2G"
        self.runkScript += f" -smp 2"
        self.runkScript += f" -kernel {self.KPath}/arch/x86/boot/bzImage"
        self.runkScript += f" -append \"console=ttyS0 root=/dev/sda earlyprintk=serial net.ifnames=0 nokaslr\""
        self.runkScript += f" -drive file={self.ImgPath}bullseye.img,format=raw"
        self.runkScript += f" -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10021-:22"
        self.runkScript += f" -net nic,model=e1000"
        self.runkScript += f" -nographic"
        self.runkScript += f" -enable-kvm"
        self.runkScript += f" -cpu host"
        self.runkScript += f" -s"
        self.runkScript += f" -pidfile {self.ImgPath}vm.pid"
        self.runkScript += f" 2>&1 | tee {self.ImgPath}vm.log"
        self.runkScript += f"\n"
    def logb(self, msgType, inMsg, quiet=False):
        endFmt = "\x1b[0m"
        startFmt = ""
        col1 = ""
        col2 = ""
        logChar = ""
        if msgType == "fail":
            col1 = "\x1b[38;5;124m"
            col2 = "\x1b[38;5;197m"
            logChar = "!"
        if msgType == "good":
            col1 = "\x1b[38;5;46m"
            col2 = "\x1b[38;5;154m"
            logChar = "+"
        if msgType == "warn":
            col1 = "\x1b[38;5;208m"
            col2 = "\x1b[38;5;220m"
            logChar = "-"
        if msgType == "info":
            col1 = "\x1b[38;5;51m"
            col2 = "\x1b[38;5;159m"
            logChar = "i"
        if msgType == "log":
            col1 = "\x1b[38;5;51m"
            col2 = "\x1b[38;5;159m"
            logChar = "+"
        if msgType == "q":
            col1 = "\x1b[38;5;63m"
            col2 = "\x1b[38;5;171m"
            logChar = "?"
        startFmt = f"{col1}[{col2}{logChar}{col1}]{col2} "
        outmsg = f"{startFmt}{inMsg}{endFmt}"
        if quiet == False:
            print(outmsg)
        return outmsg
    def run(self, cmd, rcwd=None):
        # This is a wrapper around subprocess.Popen that follows the output
        # cmd  = A list containing the command to run
        # rcwd = current working dir for this command
        # returns retcode [int]
        retcode = -1
        if rcwd == None:
            rcwd = self.BaseDir
        if cmd is not None:
            try:
                self.logb("log", f"Executing {cmd}")
                subproc = subprocess.Popen(cmd,
                                cwd=rcwd,
                                stderr=subprocess.PIPE)
                err = ''
                while subproc.poll() is None:
                    if subproc.stderr is not None:
                        line = subproc.stderr.readline().decode('utf-8')
                        err += line
                        sys.stderr.write(line)
                        sys.stderr.flush()

                exitcode = subproc.poll()
                return exitcode
            except Exception as e:
                print("[!] Error!")
                print(e)
                return retcode
    def KDownload(self):
        if self.KVersion: # This means we're downloading a mainline kernel
            version_checker = r"^([3-6])\.\d+(?:\.\d+)?$" # support major versions 3,4,5,6
            version = re.match(version_checker, self.KVersion)
            if not version:
                self.logb("fail","Invalid or unsupported kernel version!")
                return
            major_ver = version.group(1)
            full_ver = version.group(0)
            tarball_url = f"https://cdn.kernel.org/pub/linux/kernel/v{major_ver}.x/linux-{full_ver}.tar.xz"
            file_name = f"linux-{full_ver}"
            cwd = os.getcwd()
            download_path = f"{cwd}/kernel/" # TODO: Grab this from the class instead!!
            archive_name = f"{file_name}.tar.xz"
            extracted_path = download_path + file_name # This is where the kernel source is extracted, kernel/linux-version/
            archive_path = download_path + archive_name

            if os.path.isfile(archive_path):
                confirm_overwrite = self.logb("warn", f"Warning - already downloaded archive for version {full_ver}. Overwrite? [y/n] (Default=n)", quiet=True)
                archiveOverwrite = input(f"{confirm_overwrite} ")
                self.isDownloaded = False if archiveOverwrite.lower() == "y" else True # Trigger redownload
            # try to download tarball for target kernel version
            if self.isDownloaded == False:
                self.logb("good",f"Downloading {tarball_url} to {archive_path}")
                dlcmd = self.run(["curl", "-s", "--fail", tarball_url, "-o", archive_path])
                if dlcmd != 0:
                    self.logb("warn", f"Warning - attempt to download archive for kernel version {full_ver} was unsuccessful. plz check your version")
                    self.isDownloaded = False
                    return
                else:
                    self.isDownloaded = True
            if os.path.isdir(extracted_path):
                self.logb("warn", f"Warning - extracted directory already exists for version {full_ver}.")
                self.isExtracted = True
            if self.isExtracted == False:
                self.logb("good", f"Extracting the tarball for {self.KVersion}")
                self.run(["tar", "xf", archive_path, "-C", download_path])
                if not os.path.isdir(extracted_path): # Check if extracted files are where we expect
                    self.logb("warn", f"Warning - tarball downloaded to {archive_path}, but archive extraction was unsuccessful")
        else:
            self.logb("warn", f"You must set self.KVersion before using KDownload().")
    def KConfigure(self):
        cmdret = self.run(["make", "defconfig"], rcwd=self.KPath)
        cmdret = self.run(["make", "kvm_guest.config"], rcwd=self.KPath)

        self.logb("log",f"Appending {self.KConfig} to {self.KPath}.config")
        KConfigFile = open(self.KConfig, "r")
        ConfigFile = open(f"{self.KPath}.config", "a+") # This is the config file to write
        ConfigFile.write(KConfigFile.read())
        ConfigFile.close()
        KConfigFile.close()

        cmdret = self.run(["make", "olddefconfig"], rcwd=self.KPath)
    def KCompile(self):
        self.logb("warn","Warning: Building the kernel, this may take a while...")
        cmdret = self.run(["make", "-j", f"{self.nproc}"], rcwd=self.KPath)
    def DebImageBuild(self):
        self.logb("log", f"Building Debian Image - Version: {self.KVersion} Hostname: {self.KHostname}")
        try:
            self.logb("log",f"Making the debian image path {self.ImgPath}")
            os.mkdir(self.ImgPath) # this should create the dir, needs testing
        except FileExistsError:
            self.logb("warn", f"Dir exists, skipping...")
        cmdret = self.run(["cp", f"{self.BaseDir}kernel/create-image.sh", self.ImgPath])
        cmdret = self.run([f"{self.ImgPath}create-image.sh","-n", self.KHostname], rcwd=self.ImgPath)
        runkScript = open(self.runkPath, "w")
        runkScript.write(self.runkScript)
        runkScript.close()
        # make executable
        os.chmod(self.runkPath, 0o777)
        self.logb("good", f"runk.sh written to {self.runkPath}.")
        # Also need to print ssh config entry for it
    def DebImageRun(self):
        self.logb("log", f"Running Debian Image in {self.ImgPath}")
        cmdret = self.run(["/bin/bash", self.runkPath], rcwd=self.ImgPath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="easylkb - Easy Linux Kernel Builder")
    # Configuration
    parser.add_argument('-k', dest='KVersion', help='Kernel Version - Downloads a mainline kernel')
    parser.add_argument('-p', dest='KPath', help='Path to Linux kernel, use instead of -k')
    parser.add_argument('--kconfig', dest='KConfig', help='KConfig, default is example.KConfig')
    # Actions
    parser.add_argument('-d', dest='KDownload', action="store_true", help='Downloads the source of the kernel')
    parser.add_argument('-c', dest='KConfigure', action="store_true", help='Runs kernel configuration commands')
    parser.add_argument('-m', dest='KCompile', action="store_true", help='Compiles the kernel')
    parser.add_argument('-i', dest='DebImageBuild', action="store_true", help='Builds bootable Debian image from a built kernel')
    parser.add_argument('-r', dest='DebImageRun', action="store_true", help='Run image with QEMU')
    parser.add_argument('-a', dest='DoAll', action="store_true", help='Do All: Download (or use source specified by -p), Configure, Compile, Build Image, and Run Image')
    args = parser.parse_args()

    if args.KVersion is None and args.KPath is None:
        print('Please provide a kernel version with -k, or a kernel path with -p')
        exit(1)

    myKVersion = args.KVersion
    myKPath = args.KPath
    myKConfig = args.KConfig
    Kb = Kbuilder(KVersion=myKVersion, KPath=myKPath, KConfig=myKConfig)

    if args.DoAll:
        if myKPath is not None:
            args.KDownload = False # Disable download if a path is specified
        elif myKVersion is not None:
            args.KDownload = True
        else:
            print('Please provide a kernel version with -k, or a kernel path with -p')
            exit(1)
        # Set all the options
        args.KConfigure = True
        args.KCompile = True
        args.DebImageBuild = True
        args.DebImageRun = True

    if args.KDownload:
        Kb.KDownload() # Download specified kernel tarball
    if args.KConfigure:
        Kb.KConfigure() # This applies kernel configurations we need to boot and debug the kernel.
    if args.KCompile:
        Kb.KCompile() # Compile the kernel
    if args.DebImageBuild:
        Kb.DebImageBuild() # This builds the debian image from the compiled kernel
    if args.DebImageRun:
        Kb.DebImageRun()
