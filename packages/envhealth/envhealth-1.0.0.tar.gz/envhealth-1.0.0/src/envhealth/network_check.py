import requests
import os


def check_internet():
    try:
        response = requests.get("https://www.google.com", timeout=3)
        return {
            "connected": True,
            "status_code": response.status_code
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


def check_proxy():
    proxies = {
        "http": os.getenv("HTTP_PROXY"),
        "https": os.getenv("HTTPS_PROXY")
    }

    return {
        "proxy_enabled": any(proxies.values()),
        "proxies": proxies
    }
