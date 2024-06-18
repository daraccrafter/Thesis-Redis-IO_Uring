#!/bin/bash
sudo apt install -y python3-pandas python3-matplotlib
git submodule update --init --recursive
make -C redis & make -C redis-io_uring