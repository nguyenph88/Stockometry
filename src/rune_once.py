# run_once.py
from src.database import init_db
from src.scheduler import run_synthesis_and_save
import time

def run_job_now():
    """
    A simple script to run the entire analysis and output job immediately.
    """
    print("--- Starting On-Demand Job ---")
    start_time = time.time()

    # Step 1: Ensure the database is initialized and ready.
    print("\n[STEP 1] Initializing database...")
    init_db()

    # Step 2: Run the main synthesis and save function from the scheduler.
    # This will print the report to the console, save it to the DB,
    # and create the JSON output file.
    print("\n[STEP 2] Running the end-to-end analysis and output process...")
    run_synthesis_and_save()

    end_time = time.time()
    print(f"\n--- On-Demand Job Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == '__main__':
    # This block ensures the code runs when you execute the script directly.
    run_job_now()
