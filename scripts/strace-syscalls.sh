#!/bin/bash

num_calls_file="$2"
times_file="$3"
log_file="$4"
pid="$1"
touch "$num_calls_file"
touch "$times_file"
touch "$log_file"

handle_sigint() {
    sleep 1
    grep_output=$(echo "$strace_output" | grep -E 'write\([0-9]+, "\*|fdatasync|io_uring_enter')
    echo "$grep_output" >"$log_file"

    write_fds=$(echo "$grep_output" | grep 'write(' | awk -F'[()]' '{print $2}' | awk -F',' '{print $1}' | sort | uniq)
    # filter out fdatasyncs that are only for the aof file
    filtered_fdatasync=$(echo "$grep_output" | grep 'fdatasync' | while read -r line; do
        fd=$(echo "$line" | awk -F'[()]' '{print $2}' | awk -F',' '{print $1}')
        if echo "$write_fds" | grep -qw "$fd"; then
            echo "$line"
        fi
    done)

    total_time=$(echo "$grep_output" | awk '{print $NF}' | sed 's/<//;s/>//' | awk '{s+=$1} END {print (NR==0 ? "0" : s)}')
    write_time=$(echo "$grep_output" | grep 'write(' | awk '{print $NF}' | sed 's/<//;s/>//' | awk '{s+=$1} END {print (NR==0 ? "0" : s)}')
    fdatasync_time=$(echo "$filtered_fdatasync" | awk '{print $NF}' | sed 's/<//;s/>//' | awk '{s+=$1} END {print (NR==0 ? "0" : s)}')
    io_uring_enter_time=$(echo "$grep_output" | grep 'io_uring_enter' | awk '{print $NF}' | sed 's/<//;s/>//' | awk '{s+=$1} END {print (NR==0 ? "0" : s)}')

    echo "syscall,time" >"$times_file"
    echo "write,$write_time" >>"$times_file"
    echo "fdatasync,$fdatasync_time" >>"$times_file"
    echo "io_uring_enter,$io_uring_enter_time" >>"$times_file"
    echo "total,$total_time" >>"$times_file"

    fsync_count=$(echo "$filtered_fdatasync" | wc -l | tr -d ' ')
    [ -z "$fsync_count" ] && fsync_count=0

    write_count=$(echo "$grep_output" | grep -c 'write([0-9]\+, "\*' | tr -d ' ')
    [ -z "$write_count" ] && write_count=0

    io_uring_enter_count=$(echo "$grep_output" | grep -c "io_uring_enter(" | tr -d ' ')
    [ -z "$io_uring_enter_count" ] && io_uring_enter_count=0

    echo "syscall,count" >"$num_calls_file"
    echo "fdatasync,$fsync_count" >>"$num_calls_file"
    echo "write,$write_count" >>"$num_calls_file"
    echo "io_uring_enter,$io_uring_enter_count" >>"$num_calls_file"

    exit 0
}

trap handle_sigint SIGINT SIGTERM

strace_output=$(sudo strace -T -e trace=write,fdatasync,io_uring_enter -p "$pid" 2>&1)
wait
