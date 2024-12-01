import yaml

def load_config(path="config.yaml"):
    try:
        with open(path, "r") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError as e:
        print(f"Configuration file not found: {e}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error reading configuration file: {e}")
        exit(1)