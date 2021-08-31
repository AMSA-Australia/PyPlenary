import requests
import yaml

def readConfigYAMLFromHTML(fileURL):
    print("Printing Config Vars:")
    print(requests.get(fileURL).text)
    print()
    x = yaml.safe_load(requests.get(fileURL).text)
    return x