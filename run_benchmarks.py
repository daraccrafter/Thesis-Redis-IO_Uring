import os
import subprocess
import sys

def main():
    benchmarks_dir = 'Benchmarks'
    benchmark_scripts = [f for f in os.listdir(benchmarks_dir) if f.endswith('.py')]

    for script in benchmark_scripts:
        script_path = os.path.join(benchmarks_dir, script)
        print(f"Running {script_path}...")
        
        result = subprocess.run(['python3', script_path], stdout=sys.stdout, stderr=sys.stderr)

        print(f"Output of {script_path}:\n{result.stdout}")
        if result.stderr:
            print(f"Error in {script_path}:\n{result.stderr}")
        
        if result.returncode != 0:
            print(f"{script_path} failed with return code {result.returncode}")
            exit(1)
    
    print("All benchmark tests completed successfully.")
    exit(0)



if __name__ == '__main__':
    main()
