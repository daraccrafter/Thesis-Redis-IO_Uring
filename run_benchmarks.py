import os
import subprocess
import sys
import signal
import time
import argparse
from datetime import datetime

benchmark_scripts_dir = 'Benchmarks'
redis_server_command = ["./src/redis-server", "../Configs/redis/1_redis.conf"]
redis_io_uring_server_command = ["./src/redis-server", "../Configs/redis-io_uring/1_redis.conf"]

def start_redis_server(command, cwd):
    return subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_redis_server(process):
    process.send_signal(signal.SIGTERM)
    process.wait()

def signal_handler(sig, frame):
    print('Interrupt received, shutting down servers...')
    stop_redis_server(redis_server_process)
    stop_redis_server(redis_io_uring_server_process)
    sys.exit(0)

def run_benchmark_script(script, timestamp, iterations):
    script_path = os.path.join(benchmark_scripts_dir, script)
    print(f"Running {script_path} with timestamp {timestamp} for {iterations} iterations...")
    
    result = subprocess.run(['python3', script_path, timestamp, str(iterations)], stdout=sys.stdout, stderr=sys.stderr)

    if result.returncode != 0:
        print(f"{script_path} failed with return code {result.returncode}")
        stop_redis_server(redis_server_process)
        stop_redis_server(redis_io_uring_server_process)
        sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

redis_server_process = start_redis_server(redis_server_command, cwd="redis")
redis_io_uring_server_process = start_redis_server(redis_io_uring_server_command, cwd="redis-io_uring")
time.sleep(1)

try:
    parser = argparse.ArgumentParser(description="Run benchmark scripts.")
    parser.add_argument('script', nargs='?', help="The specific benchmark script to run")
    parser.add_argument('--iterations', type=int, default=1, help="Number of times to run the benchmark script")
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if args.script:
        run_benchmark_script(args.script, timestamp, args.iterations)
    else:
        benchmark_scripts = [f for f in os.listdir(benchmark_scripts_dir) if f.endswith('.py')]
        for script in benchmark_scripts:
            run_benchmark_script(script, timestamp, args.iterations)
finally:
    stop_redis_server(redis_server_process)
    stop_redis_server(redis_io_uring_server_process)

print("All benchmark tests completed successfully.")
sys.exit(0)

if __name__ == '__main__':
    main()
