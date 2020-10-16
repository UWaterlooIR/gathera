import json

import requests
from config.settings.base import SEARCH_SERVER_IP
from config.settings.base import SEARCH_SERVER_PORT
from config.settings.base import INDEX_NAME
from config.settings.base import DEFAULT_NUM_DISPLAY
from web.interfaces.SearchEngine.base import SearchInterface
from collections import OrderedDict


class Elastic(SearchInterface):
    headers = {'Accept': 'application/json', 'Content-type': 'application/json'}
    url = f"http://{SEARCH_SERVER_IP}:{SEARCH_SERVER_PORT}/{INDEX_NAME}"

    @staticmethod
    def search(query: str, size: int = DEFAULT_NUM_DISPLAY, offset: int = 0):
        response = requests.get(
            f"{Elastic.url}/_search",
            data=json.dumps({
                "query": {
                    "match": {
                        "contents": query
                    }
                },
                "size": size,
                "from": offset,
                "highlight": {
                    "fields": {
                        "contents": {}
                    }
                }
            }),
            headers=Elastic.headers
        )

        response.raise_for_status()
        response_json = response.json()
        hits = [
            {
                "rank": i,
                "docno": hit["_id"],
                "score": hit["_score"],
                "title": hit["_source"]["contents"][:15],
                "snippet": '... ' + ' ... '.join(hit["highlight"]["contents"]) + '... '
            }
            for i, hit in enumerate(response_json["hits"]["hits"])
        ]
        return {
            "query": query,
            "total_matches": len(response_json["hits"]["hits"]),
            "size": size,
            "total_time": response_json["took"] / 1000,
            "hits": hits
        }

    @staticmethod
    def get_content(docno: str):
        response = requests.get(
            f"{Elastic.url}/_doc/{docno}/_source/",
            headers=Elastic.headers
        )
        response.raise_for_status()
        response_json = response.json()
        return {
            "docno": response_json["id"],
            "raw": response_json["contents"]
        }

    @staticmethod
    def get_raw(docno: str):
        response = requests.get(
            f"{Elastic.url}/_doc/{docno}/_source/",
            headers=Elastic.headers
        )
        response.raise_for_status()
        response_json = response.json()
        return {
            "docno": response_json["id"],
            "raw": response_json["raw"]
        }
