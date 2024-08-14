#!/bin/bash

num_calls_file="$2"
times_file="$3"
log_file="$4"
pid="$1"
touch "$num_calls_file"
touch "$times_file"
touch "$log_file"

handle_sigint() {
    echo "SIGINT received. Processing and generating reports..."
    sleep 1
    strace_output=$(echo "$strace_output" | grep -E 'write\([0-9]+, "\*|fdatasync|io_uring_enter')
    echo "$strace_output" >"$log_file"

    pids=$(echo "$strace_output" | grep -oP '\[pid \K[0-9]+<[^>]+>' | sort | uniq)

    echo "Captured PIDs:"
    echo "$pids"

    echo "process_name,write,fdatasync,io_uring_enter" >"$num_calls_file"
    echo "process_name,write_time,fdatasync_time,io_uringenter_time,write_avg,fdatasync_avg,io_uringenter_avg,write_std,fdatasync_std,io_uringenter_std,total_time" >"$times_file"

    for pid_with_name in $pids; do
        pid=$(echo "$pid_with_name" | grep -oP '^[0-9]+')
        process_name=$(echo "$pid_with_name" | grep -oP '<\K[^>]+')

        echo "Processing process: $process_name (PID: $pid)"
        write_count=$(echo "$strace_output" | grep -c "\[pid $pid<$process_name>\].*write")
        fdatasync_count=$(echo "$strace_output" | grep -c "\[pid $pid<$process_name>\].*fdatasync")
        iouringenter_count=$(echo "$strace_output" | grep -c "\[pid $pid<$process_name>\].*io_uring_enter")

        write_count=${write_count:-0}
        fdatasync_count=${fdatasync_count:-0}
        iouringenter_count=${iouringenter_count:-0}

        write_time=$(echo "$strace_output" | grep "\[pid $pid<$process_name>\].*write" | awk '{print $NF}' | tr -d '<>' | awk '{s+=$1; print $1} END {print "total="s}')
        fdatasync_time=$(echo "$strace_output" | grep "\[pid $pid<$process_name>\].*fdatasync" | awk '{print $NF}' | tr -d '<>' | awk '{s+=$1; print $1} END {print "total="s}')
        iouringenter_time=$(echo "$strace_output" | grep "\[pid $pid<$process_name>\].*io_uring_enter" | awk '{print $NF}' | tr -d '<>' | awk '{s+=$1; print $1} END {print "total="s}')

        write_total_time=$(echo "$write_time" | grep "total=" | cut -d= -f2)
        fdatasync_total_time=$(echo "$fdatasync_time" | grep "total=" | cut -d= -f2)
        iouringenter_total_time=$(echo "$iouringenter_time" | grep "total=" | cut -d= -f2)

        write_total_time=${write_total_time:-0}
        fdatasync_total_time=${fdatasync_total_time:-0}
        iouringenter_total_time=${iouringenter_total_time:-0}

        if [ "$write_count" -gt 0 ]; then
            write_avg=$(echo "scale=6; $write_total_time / $write_count" | bc)
        else
            write_avg=0
        fi

        if [ "$fdatasync_count" -gt 0 ]; then
            fdatasync_avg=$(echo "scale=6; $fdatasync_total_time / $fdatasync_count" | bc)
        else
            fdatasync_avg=0
        fi

        if [ "$iouringenter_count" -gt 0 ]; then
            iouringenter_avg=$(echo "scale=6; $iouringenter_total_time / $iouringenter_count" | bc)
        else
            iouringenter_avg=0
        fi

        write_std=0
        if [ "$write_count" -gt 1 ]; then
            write_std=$(echo "$write_time" | grep -v "total=" | awk -v avg=$write_avg '{sum+=($1-avg)^2} END {print sqrt(sum/NR)}')
        fi

        fdatasync_std=0
        if [ "$fdatasync_count" -gt 1 ]; then
            fdatasync_std=$(echo "$fdatasync_time" | grep -v "total=" | awk -v avg=$fdatasync_avg '{sum+=($1-avg)^2} END {print sqrt(sum/NR)}')
        fi

        iouringenter_std=0
        if [ "$iouringenter_count" -gt 1 ]; then
            iouringenter_std=$(echo "$iouringenter_time" | grep -v "total=" | awk -v avg=$iouringenter_avg '{sum+=($1-avg)^2} END {print sqrt(sum/NR)}')
        fi

        total_time=$(echo "$write_total_time + $fdatasync_total_time + $iouringenter_total_time" | bc)

        echo "$process_name,$write_count,$fdatasync_count,$iouringenter_count" >>"$num_calls_file"
        echo "$process_name,$write_total_time,$fdatasync_total_time,$iouringenter_total_time,$write_avg,$fdatasync_avg,$iouringenter_avg,$write_std,$fdatasync_std,$iouringenter_std,$total_time" >>"$times_file"
    done

    exit 0
}

trap handle_sigint SIGINT SIGTERM

strace_output=$(sudo strace -f -T --decode-pids=comm -e trace=write,fdatasync,io_uring_enter -p "$pid" 2>&1)

echo "$strace_output"

wait
