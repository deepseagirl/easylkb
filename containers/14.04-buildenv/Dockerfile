FROM ubuntu:14.04

RUN apt-get update && apt-get install -y build-essential curl make gcc gcc flex bison libncurses-dev libelf-dev libssl-dev debootstrap bc python3 gcc-4.8-multilib libc6-dev-i386
RUN mkdir /build /toolchain
RUN ln -s `which gcc` /toolchain/gcc

ENV ENV PATH="/toolchain:$PATH"
WORKDIR /build
