from scriptation.preprocessor import Preprocessor
from scriptation.scheduler import Scheduler
from scriptation.executor import Executor

import logging

logging.basicConfig(level=logging.INFO)
    
preprocessor = Preprocessor("/home/shinapri/Documents/quantum-espresso/scriptation-2/config/qe.json")
scheduler = Scheduler(preprocessor)

executor = Executor()
executor.execute_batch(scheduler)