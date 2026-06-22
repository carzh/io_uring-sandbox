import argparse
import subprocess
import time
import pandas as pd
import os
import sys

def main():
    # 1. Setup Command Line Arguments
    parser = argparse.ArgumentParser(description="Run Docker benchmark and capture total execution time.")
    parser.add_argument('--runtime', required=True, help="Name of the docker runtime (e.g., runsc, runc)")
    parser.add_argument('--io-uring', action='store_true', help="Flag to enable io_uring")
    parser.add_argument('--csv-file', default='benchmark_results.csv', help="Optional: Name of the output CSV file")
    parser.add_argument('--runs', type=int, default=100, help="Optional: Number of times to run the container")
    
    args = parser.parse_args()

    print(f"--- Starting Benchmark ---")
    print(f"Runtime: {args.runtime}")
    print(f"io_uring enabled: {args.io_uring}")
    print(f"Target CSV: {args.csv_file}")
    print(f"Total Runs: {args.runs}\n")

    # 2. Base Docker Command
    cmd = ["docker", "run", "--rm", f"--runtime={args.runtime}"]
    if args.io_uring:
        cmd.extend(["--env", "UV_USE_IO_URING=1"])
    cmd.append("node-uring-bench") # Ensure this matches your built image name

    run_times = []

    # 3. Execute the Runs
    for i in range(1, args.runs + 1):
        print(f"Executing run {i}/{args.runs}...", end="", flush=True)
        
        # Record start time
        start_time = time.perf_counter()
        
        # Run the container (suppress stdout/stderr to keep console clean, or remove stdout/stderr args to see Node output)
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Record end time
        end_time = time.perf_counter()
        
        if result.returncode != 0:
            print(f" [FAILED] - Container exited with code {result.returncode}")
            sys.exit(1)
            
        elapsed = end_time - start_time
        run_times.append(elapsed)
        print(f" [{elapsed:.4f} seconds]")

    # 4. Format the Data for Pandas
    # Define the column name based on runtime and io_uring status
    column_name = f"{args.runtime}_iouring_{'enabled' if args.io_uring else 'disabled'}"
    
    # Create a DataFrame for the current execution
    new_data = pd.DataFrame({
        'Run': range(1, args.runs + 1),
        column_name: run_times
    })

    # 5. Handle CSV Logic (Create or Append Column)
    if os.path.exists(args.csv_file):
        print(f"\nFound existing {args.csv_file}. Appending as a new column...")
        existing_df = pd.read_csv(args.csv_file)
        
        # If the column already exists from a previous run, drop it so we can overwrite with fresh data
        if column_name in existing_df.columns:
            existing_df = existing_df.drop(columns=[column_name])
            
        # Merge on the 'Run' column (uses outer join just in case previous runs had a different amount of iterations)
        final_df = pd.merge(existing_df, new_data, on='Run', how='outer')
    else:
        print(f"\nCreating new file: {args.csv_file}")
        final_df = new_data

    # Sort by Run number just to keep it clean, and save to CSV
    final_df = final_df.sort_values(by='Run')
    final_df.to_csv(args.csv_file, index=False)
    
    print(f"\nSuccess! Data saved to {args.csv_file}")

if __name__ == "__main__":
    main()

