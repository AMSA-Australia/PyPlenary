import requests
import yaml

def readConfigYAMLFromHTML(fileURL):
    x = yaml.load(requests.get(fileURL).text)
    return x