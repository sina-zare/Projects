from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import requests
from bs4 import BeautifulSoup
import re

script_name = 'price_extractor'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
registry = CollectorRegistry()

# Service Specific Metrics
current_price = Gauge(
    'current_price',
    'current price of index',
    ['index'],
    registry=registry
)

# Target URL
urls = {
    'gold' : "https://www.tgju.org/profile/geram18",
    'usd' : "https://www.tgju.org/profile/price_dollar_rl"
}


# Set a reasonable User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
try:
    for url_key, url_value in urls.items():
        # Fetch the page
        response = requests.get(url_value, headers=headers)
        response.raise_for_status()
        html = response.text

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Look for text matching "نرخ فعلی"
        text = soup.get_text()

        # Regular expression for the numeric value
        match = re.search(r"نرخ فعلی[:\s]*([0-9,]+)", text)
        if match:
            value = match.group(1)
            clean_value = int(int(value.replace(',', ''))/10)
            print(f"{url_key.upper()} Current Price: {clean_value}")

            current_price.labels(index=url_key).set(clean_value)

        else:
            print("Value not found")
            #current_price.labels(index=url_key).set(0)

except Exception as err:
    print(f"Script failed: {err}")
    #current_price.labels(index=url_key).set(0)

finally:

    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance},
        registry=registry
    )

    print('\n✅ Metrics Sent.')