import yaml
import urllib
from urllib import request

def readConfigYAMLFromHTML(fileURL):
    x = yaml.safe_load(urllib.request.urlopen(fileURL))
    return x