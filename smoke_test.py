"""
PSIT smoke test -- run against the deployed Streamlit Cloud URL.
Usage: python smoke_test.py https://YOUR-APP.streamlit.app
"""
import sys
import requests

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    return condition

def main():
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <deployed-url>")
        sys.exit(1)

    url = sys.argv[1].rstrip("/")
    print(f"\nRunning smoke test against: {url}\n")

    try:
        resp = requests.get(url, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Could not reach {url}: {e}")
        sys.exit(1)

    text = resp.text
    results = [
        check("HTTP 200 response",                   resp.status_code == 200),
        check("Streamlit app shell in response",     "streamlit" in text.lower()),
        check("Streamlit static assets present",      "static/js" in text or "_stcore" in text),
        check("No crash traceback in response",      "Traceback (most recent call last)" not in text),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
