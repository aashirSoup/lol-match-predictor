# amount of files


from pathlib import Path
print(len(list(Path("data/raw").glob("*.json"))))