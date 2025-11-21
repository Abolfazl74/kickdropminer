import argparse
import asyncio
import sys
from worker import run_farming

def main(category_id, mode, log_callback=None):
    if log_callback is None:
        def log_callback(msg):
            print(msg, flush=True)
            
    try:
        asyncio.run(run_farming(mode, category_id, log_callback=log_callback))
    except KeyboardInterrupt:
        log_callback("Farmer stopped by user.")
    except Exception as e:
        log_callback(f"Fatal error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, required=True)
    parser.add_argument("--mode", type=str, default="streamers")
    args = parser.parse_args()
    
    main(args.category, args.mode)