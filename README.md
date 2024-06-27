# Thesis-Redis-IO_Uring

This repository contains the code and scripts for evaluating Redis with IO_uring for my thesis.The project includes the redis repository as a git submodule. Also it includes my implementation with io_uring as a git submodule (found here: https://github.com/daraccrafter/redis-io_uring/tree/unstable)

## Scripts

The benchmarking and data persistence test scripts are located in the `scripts` directory. Below is a detailed explanation of the main scripts and their functionalities.

### Benchmarking Scripts

- **`run_benchmarks.py`**: This script is designed to run benchmarks for different Redis modes and persistence configurations. It offers several command-line arguments for flexibility:
  - `--iterations <arg>`: Specifies the number of iterations for each benchmark. The data generated from each run is averaged over all iterations.
  - `--plot`: Generates comparison graphs for analysis, useful for inclusion in a thesis or report.

  **Usage Examples**:
  - To run benchmarks with 3 iterations and generate plots:
    ```sh
    python3 run_benchmarks.py --iterations 3 --plot
    ```
  - To run specific benchmark scripts located in the `benchmarks/AOF` directory and the `rps.py` script in the `benchmarks/URING_AOF` directory:
    ```sh
    python3 run_benchmarks.py --iterations 3 --plot benchmarks/AOF benchmarks/URING_AOF/rps.py
    ```
  - To run all benchmark scripts for a single iteration and generate plots:
    ```sh
    python3 run_benchmarks.py --plot
    ```

### Data and Logs

- **Benchmark Data**: Each Redis configuration directory stores its respective benchmark data. For example, data for the AOF configuration is stored in `benchmarks/<config>/csvs`.
- **Logs**: Logs from different Python scripts, including the latest Redis server logs, are stored in the same directories. For example, logs for the AOF configuration are found in `benchmarks/<config>/logs`.
- **Temporary Directory**: The `temp` directory is used for the current Redis instance to generate the AOF file. This allows for manual inspection if needed.

## Prerequisites
Firstly make sure your kernel version is >= 5.4 to support liburing.
## Installing Dependencies and building
### Ubuntu
If your on ubuntu you can just run ./setup.sh 
### Manually installing dependencies
Before you begin, ensure you have the following installed on your system:

- `make`
- `gcc`
- `python3`
- Python libraries: `pandas`, `psutil`, `matplotlib`, `redis`
- `pip` (if installing)

You can install the Python dependencies using pip:

```sh
pip install pandas psutil matplotlib redis
```