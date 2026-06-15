import requests
from bs4 import BeautifulSoup
import json

def get_public_ip():
    url = "https://ipmyp.ir"
    response = requests.get(url, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")

    div = soup.find("div", class_="ipvj-lite-box")
    ip = div["data-initial-ip"]
    data = {"ip": ip}
    print(json.dumps(data, indent=2))
    return data

get_public_ip()
