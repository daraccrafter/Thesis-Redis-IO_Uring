#!/bin/bash
git submodule update --init --recursive
make -C redis & make -C redis-io_uring