# Thesis-Redis-IO_Uring

This repository contains the code and scripts for evaluating Redis with `io_uring` as part of my thesis. The project integrates the official [`redis`](https://github.com/redis/redis) repository as a git submodule. Additionally, it includes my custom implementation as a git submodule [`redis-io_uring`](https://github.com/daraccrafter/redis-io_uring/tree/unstable).

## Prerequisites

Before getting started, ensure your system meets the following requirements:

- **Kernel Version**: Ensure your kernel version is >= 6.x.

## Installing Dependencies and Building

### Ubuntu & Debian-based

Run the `./setup.sh` script. This script will:

1. Pull both `redis` and `redis-io_uring` git submodules, if not already pulled.
2. Install all necessary dependencies.
3. Build both `redis` and `redis-io_uring`.

Simply execute the following command in your terminal:

```sh
./setup.sh
```

### Manually Installing Dependencies

If you prefer to install dependencies manually, ensure you have the following installed on your system:

- `make`
- `gcc`
- `python3`
- Python libraries: `pandas`, `psutil`, `matplotlib`, `redis` (You can also install these with `pip3`)

Follow these steps:

1. **Pull Git Submodules**:

   If you didn't pull the repository with `--recurse-submodules`, initialize and update the submodules:

   ```sh
   git submodule update --init --recursive
   ```

2. **Build Redis and Redis-IO_Uring**:

   Navigate to the project root directory and run the following commands to build `redis` and `redis-io_uring`:

   ```sh
   make -C redis
   make -C redis-io_uring
   ```

3. **Copy Redis Tools**:

   Copy the `redis-benchmark` and `redis-check-aof` tools to the `scripts` directory:

   ```sh
   cp redis/src/redis-benchmark scripts/
   cp redis/src/redis-check-aof scripts/
   ```

## Running Redis

To run Redis, navigate to either the `redis` or `redis-io_uring` directory and execute the following command:

```sh
./src/redis-server redis.conf
```

### Configuration Options redis-io_uring

Additional configuration options can be set in the `redis.conf` file. Here are the liburing configurations for append-only file operations:

    appendonly-liburing yes
    liburing-queue-depth xl
    liburing-retry-count xl
    liburing-sqpoll no
    correct-test no
    correct-test-reqnum 100000

### Running redis-benchmark

To run the benchmark tests, use the `redis-benchmark` tool [here](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/):

```sh
./src/redis-benchmark -t set,incr -n 500000 -q
```

This command will run benchmark tests for the set and incr operations with 500,000 requests, providing a quick summary of the results.

## Scripts

### Benchmarks
First, navigate to the `scripts` directory by executing:
```sh
cd scripts
```
Ensure that the directory contains the necessary executables:
redis-benchmark
redis-check-aof

To run the benchmark without reformatting the filesystem, execute the following command:
```sh
sudo python3 run_benchmarks.py --requests 4000000
```
To run the benchmark with reformatting between each test, follow these steps:
```sh
cp -r data/RDB-<timestamp> <root-partition>
sudo umount /mnt/ext4
sudo mkfs -t ext4 /dev/<drive>
sudo mount /mnt/ext4
# REPEAT INSTALLATION
sudo python3 run_benchmarks.py --benchmark AOF --requests 4000000
cp -r data/AOF-all-<timestamp> <root-partition>
sudo umount /mnt/ext4
sudo mkfs -t ext4 /dev/<drive>
sudo mount /mnt/ext4
# REPEAT INSTALLATION
sudo python3 run_benchmarks.py --benchmark URING_AOF --requests 4000000
```
Repeat this sequence three times to achieve results comparable to those presented in the evaluation.

**IMPORTANT!** Execute the benchmarks with elevated privileges because `strace` requires these privileges to function properly.

**Benchmark Data:** Each Redis configuration directory stores its respective benchmark data, typically located in `benchmarks/<config>/data`.

**Arguments**:
- `--benchmark`: Specifies which benchmark to run. Options include:
  - **AOF**: Runs the Append-Only File benchmark.
  - **RDB**: Runs the Redis Database benchmark.
  - **URING_AOF**: Runs the benchmark using `io_uring` with AOF.
  
  If no benchmark is specified, the script will run all three benchmarks by default.
  
- `--requests`: Specifies the number of requests to be sent during the benchmark. The default is `100,000`, but for a more extensive test, you can increase this number as shown in the example (`4,000,000` requests).
  
- `--fsync`: Defines the `fsync` mode for the AOF benchmark. Available options include:
  - **always**: Ensures that data is written to disk immediately after each write operation.
  - **everysec**: Synchronizes data to disk every second.
  - **no**: Disables synchronization after write operations.
  - **all**: Runs the benchmark for all `fsync` modes.
  
  The default setting is `all`.
  
- `--no-strace`: When this flag is set, the benchmark runs without invoking `strace`, which can reduce overhead and improve performance during the tests. By default, `strace` is used.

### Data Correctness Test
Navigate to the `scripts` directory:
```sh
cd scripts
```
To verify the correctness of the data, and run the 3 mentioned tests, you can execute the following 
command in the terminal:
```sh
sudo python3 correctness-test.py
```
**Arguments**:
- `--requests`: Specifies the number of requests to be used in the benchmark. The default value is `100,000`, but you can adjust this number depending on the scope of your testing.
  
- `--no-bgrewriteaof`: This flag, if set, disables the triggering of the `BGREWRITEAOF` command during the test. The `BGREWRITEAOF` command is typically used to rewrite the AOF (Append Only File) to reduce its size and optimize its structure. By default, this feature is enabled, but you can disable it with this flag to test scenarios without AOF rewriting.

### Plotting
To generate plots navigate to the `scripts` directory:
```sh
cd scripts
```
And execute the script:
```sh
sudo python3 plot.py --dir_rdb <path> --dir_aof <path> --dir_uring <path> --dir <output-dir> --type all
```

The directories for each persistence mode can contain many sub directories (for each run) generated by the benchmark. For example if you run the benchmark without reformatting you can just execute:
```sh
sudo python3 plot.py --dir_rdb benchmark/RDB/data --dir_aof benchmark/AOF/data --dir_uring benchmark/URING_AOF/data --dir ./output --type all
```
This will generate all the graphs.

**Arguments**:
- `--dir_rdb`: Specifies the directory containing the CSV files for the **RDB** persistence mode. This argument is mandatory.
  
- `--dir_aof`: Specifies the directory containing the CSV files for the **AOF** persistence mode. This argument is mandatory.
  
- `--dir_uring`: Specifies the directory containing the CSV files for the **URING_AOF** persistence mode. This argument is mandatory.
  
- `--dir`: Defines the directory where the generated graphs will be saved. The default is the current directory.
  
- `--type`: Specifies the type of graph to plot. The following options are available:
  - `rps`: Generates a graph comparing the requests per second (RPS) across the different persistence modes.
  - `cpu`: Generates a graph comparing CPU usage across the different persistence modes.
  - `memory`: Generates a graph comparing memory usage across the different persistence modes.
  - `latency`: Generates a graph comparing latency statistics across the different persistence modes.
  - `all`: Generates all of the above graphs.
