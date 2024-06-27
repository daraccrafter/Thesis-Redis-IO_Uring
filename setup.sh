#!/bin/sh

sudo apt-get install build-essential -y
sudo apt install -y python3 python3-pandas python3-matplotlib python3-psutil python3-redis -y
git submodule update --init --recursive
make -C redis & make -C redis-io_uring
cp redis/src/redis-benchmark src/
cp redis/src/redis-check-aof src/