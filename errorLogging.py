import json
import time
from json.decoder import JSONDecodeError


def write_json(error_log: dict, dictionaryKey=int, filename="upsert_logs.json"):

    try:
        with open(filename, "r+") as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join error_log with file_data inside emp_details
            file_data[str(dictionaryKey)].append(error_log[dictionaryKey][0])
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            json.dump(file_data, file, indent=4)
            # Close the file
            file.close()
    except (FileNotFoundError, JSONDecodeError):
        # If the file doesn't exist or is empty, create it and write the data to it.
        with open(filename, "w") as file:
            json.dump(error_log, file, indent=4)
            file.close()


def clean_log():
    """cleans error log file"""
    with open("upsert_logs.json", "w") as f:
        f.write("")
        f.close()


def check_log() -> bool:
    """checks if error log file is not empty"""
    try:
        with open("upsert_logs.json", "r") as f:
            data = json.load(f)
            f.close()

        return True if len(data) > 0 else False
    except (FileNotFoundError, JSONDecodeError):
        return False
