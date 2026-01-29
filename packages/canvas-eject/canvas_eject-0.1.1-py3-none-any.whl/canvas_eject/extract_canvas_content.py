import re
import json
import httpx
import ast
import sys

_SSR_PATTERN = re.compile(
    r'window\.__reactRouterContext\.streamController\.enqueue\((".+?routes\/canvas\.shared\.\$sharedTextdocId.+?\")\);\s*<'
)
_CANVAS_URL_PATTERN = re.compile(r"https:\/\/chatgpt\.com\/canvas\/shared\/\w+")


def retrieve_published_page(url: str) -> str:
    r = httpx.get(url)
    r.raise_for_status()
    return r.text


def extract_react_router_ssr_serialized_responses(html: str) -> list:
    # WARNING: This *WILL* break in near future!
    match = _SSR_PATTERN.search(html)
    inner = match.group(1)
    unescaped = ast.literal_eval(inner)
    events = json.loads(unescaped)
    return events


def unfurl_encoded_object(jumbo: list, encoded_object: dict) -> dict:
    decoded: dict = {}
    for k, v in encoded_object.items():
        if type(k) is str and k.startswith("_"):
            id = int(k[1:])
            decoded[jumbo[id]] = (
                jumbo[v] if v >= 0 else v
            )  # this is probably incorrect but we don't care
    return decoded


def extract_canvas_content(url: str):
    if not _CANVAS_URL_PATTERN.match(url):
        print(f"Error: Provided URL {url} is not a ChatGPT shared canvas")
        raise ValueError
    content = retrieve_published_page(url)
    events = extract_react_router_ssr_serialized_responses(content)
    request_id = events.index("routes/canvas.shared.$sharedTextdocId")
    encoded_response = events[request_id + 1]
    decoded_response = unfurl_encoded_object(events, encoded_response)
    return decoded_response["content"]


if __name__ == "__main__":
    print(extract_canvas_content(sys.argv[1]))

