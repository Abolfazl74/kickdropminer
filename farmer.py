import asyncio
import sys
import os

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
    if sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)

from worker import run_farming

import argparse

def main(category, mode, log_callback=None):
    asyncio.run(run_farming(mode, category, log_callback=log_callback))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=int, required=True)
    parser.add_argument('--mode', required=True)
    args = parser.parse_args()

    main(args.category, args.mode)