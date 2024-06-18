#!/bin/bash

REDIS_DIR="redis"
REDIS_IO_URING_DIR="redis-io_uring"
CONFIG_DIR="Configs"

git submodule update --init --recursive
make -C redis & make -C redis-io_uring
mkdir -p $REDIS_IO_URING_DIR/$CONFIG_DIR & mkdir -p $REDIS_DIR/$CONFIG_DIR
cp $CONFIG_DIR/$REDIS_IO_URING_DIR/* $REDIS_IO_URING_DIR/$CONFIG_DIR & cp $CONFIG_DIR/$REDIS_DIR/* $REDIS_DIR/$CONFIG_DIR