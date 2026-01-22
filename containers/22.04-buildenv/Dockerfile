FROM ubuntu:22.04

RUN apt-get update && apt-get install -y build-essential python3 curl make gcc flex bison libncurses-dev libelf-dev libssl-dev debootstrap bc
RUN mkdir /build /toolchain
RUN ln -s `which gcc` /toolchain/gcc

ENV ENV PATH="/toolchain:$PATH"
WORKDIR /build
