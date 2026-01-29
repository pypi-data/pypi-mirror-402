from urllib.parse import urlparse
def extract_hostname(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

