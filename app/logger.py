import logging
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'app.log')
LOG_FILE = os.path.abspath(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("motoriq")
