import os
import subprocess

def main():
    tests_dir = 'Tests'
    benchmark_scripts = [f for f in os.listdir(tests_dir) if f.endswith('.py')]

    for script in benchmark_scripts:
        script_path = os.path.join(tests_dir, script)
        print(f"Running {script_path}...")
        
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        
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
