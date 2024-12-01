import yaml
import numpy as np


def load_face_encodings(path="encoding_face.yaml"):
    """
    Load dữ liệu từ file face_encoding.yaml.
    :param path: Đường dẫn đến file YAML.
    :return:
    """
    try:
        with open(path, "r") as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError as e:
        print(f"Encoding file not found: {e}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error reading encoding file: {e}")
        exit(1)
