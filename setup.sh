#!/bin/bash
sudo apt install -y python3-pandas python3-matplotlib psutil
git submodule update --init --recursive
make -C redis & make -C redis-io_uring
cp redis/src/redis-benchmark .