import requests
import yaml

def readConfigYAMLFromHTML(fileURL):
    x = yaml.safe_load(requests.get(fileURL).text)
    return x