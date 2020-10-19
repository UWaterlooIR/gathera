import requests
from config.settings.base import DEFAULT_NUM_DISPLAY
from config.settings.base import SEARCH_SERVER_IP
from config.settings.base import SEARCH_SERVER_PORT
from web.interfaces.SearchEngine.base import SearchInterface


class Anserini(SearchInterface):

    @staticmethod
    def search(query: str, size: int = DEFAULT_NUM_DISPLAY, offset: int = 0):
        response = requests.get(
            f"http://{SEARCH_SERVER_IP}:{SEARCH_SERVER_PORT}/search",
            params={
                "query": query,
                "size": offset + size,
            }
        )
        response.raise_for_status()
        response_json = response.json()
        response_json["hits"] = response_json["hits"][offset:offset+size]
        return response_json

    @staticmethod
    def get_content(docno: str):
        response = requests.get(
            f"http://{SEARCH_SERVER_IP}:{SEARCH_SERVER_PORT}/docs/{docno}/content",
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json

    @staticmethod
    def get_raw(docno: str):
        response = requests.get(
            f"http://{SEARCH_SERVER_IP}:{SEARCH_SERVER_PORT}/docs/{docno}/raw",
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json
