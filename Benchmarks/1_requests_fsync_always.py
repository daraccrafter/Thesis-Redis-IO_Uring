import subprocess
import os
import sys
import pandas as pd
benchmark = "1_requests_fsync_always"
request_counts = [1000,10000]

base_dir = "csvs"
redis_dir = os.path.join(base_dir, "redis")
redis_io_uring_dir = os.path.join(base_dir, "redis-io_uring")

os.makedirs(redis_dir, exist_ok=True)
os.makedirs(redis_io_uring_dir, exist_ok=True)

if len(sys.argv) != 3:
    print("Usage: python3 benchmark_script.py <timestamp> <iterations>")
    sys.exit(1)

timestamp = sys.argv[1]
iterations = int(sys.argv[2])

output_dir_redis = os.path.join(redis_dir, f"1_{timestamp}")
output_dir_redis_io_uring = os.path.join(redis_io_uring_dir, f"1_{timestamp}")

os.makedirs(output_dir_redis, exist_ok=True)
os.makedirs(output_dir_redis_io_uring, exist_ok=True)

def run_benchmark(request_count, output_dir, port, iteration):
    csv_filename = os.path.join(output_dir, f"{request_count}_numrequests_run{iteration}.csv")
    command = ["redis-benchmark", "-p", str(port), "-t", "set", "-n", str(request_count), "--csv"]
    
    with open(csv_filename, "w") as csvfile:
        subprocess.run(command, stdout=csvfile, check=True)

def average_csv_files(request_count, output_dir, iterations):
    files = [os.path.join(output_dir, f"{request_count}_numrequests_run{i}.csv") for i in range(1, iterations + 1)]
    df_list = [pd.read_csv(file) for file in files]
    
    df_combined = pd.concat(df_list)
    df_avg = df_combined.groupby('test').mean().reset_index()
    
    avg_csv_filename = os.path.join(output_dir, f"{request_count}_numrequests_avg.csv")
    df_avg.to_csv(avg_csv_filename, index=False)
    print(f"Average results saved to {avg_csv_filename}")

if __name__ == '__main__':
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis...")
            run_benchmark(count, output_dir_redis, 6380, i)
        
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis io_uring...")
            run_benchmark(count, output_dir_redis_io_uring, 6379, i)

    for count in request_counts:
        average_csv_files(count, output_dir_redis, iterations)
        average_csv_files(count, output_dir_redis_io_uring, iterations)

    print(f"{benchmark} data has been saved in {output_dir_redis} and {output_dir_redis_io_uring}")
