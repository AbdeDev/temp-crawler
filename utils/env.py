from dotenv import load_dotenv
import os

load_dotenv()

CHROME_EXECUTABLE = os.getenv('CHROME_EXECUTABLE_PATH')
ENABLE_LOG = os.getenv("ENABLE_LOG")
