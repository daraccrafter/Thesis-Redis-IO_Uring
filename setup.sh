#!/bin/bash

sudo apt-get install build-essential
sudo apt install -y python3 python3-pandas python3-matplotlib python3-psutil python3-redis
git submodule update --init --recursive
make -C redis & make -C redis-io_uring
cp redis/src/redis-benchmark src/
cp redis/src/redis-check-aof src/