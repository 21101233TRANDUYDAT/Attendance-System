from utils.config import load_config
import os


if __name__  == "__main__":
    config = load_config()
    print("firebase URL: ", config["firebase"]["database_url"])
    print("check-out time: ", config["time"]["check_out_time"])
    print("similarity_threshold: ", config["recognition"]["similarity_threshold"])