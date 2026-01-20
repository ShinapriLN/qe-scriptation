from scriptation.preprocessor import Preprocessor
from scriptation.scheduler import Scheduler
from scriptation.executor import Executor

import logging
import time
import argparse
import os, sys

def main(path):
    preprocessor = Preprocessor(path)
    scheduler = Scheduler(preprocessor)

    executor = Executor()
    executor.execute_batch(scheduler)


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="path of the json config file.")

    args = parser.parse_args()

    start_time = time.time()

    path = args.path
    main(path)

    logging.info(f"\n\n     🫡  [FINISH] total time usage... {time.time() - start_time:.3f}s")
