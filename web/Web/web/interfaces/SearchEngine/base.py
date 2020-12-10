from abc import ABC
from abc import abstractmethod


class SearchInterface(ABC):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        super().__init__()

    @staticmethod
    @abstractmethod
    def search(query: str, size: int, offset: int) -> dict:
        """Returns a list of a dict of search results for a given query.
        E.g.
        {
            "query": "submitted query",
            "total_time": "0.238293",
            "total_matches": 10,
            "hits": [
                {
                    "rank": 1
                    "docno": "92302",
                    "score": "34239",
                    "title": "Title of document",
                    "snippet": "A short highlight of the document based on the query"
                },
        }
        """
        pass

    @staticmethod
    @abstractmethod
    def get_content(docno: str) -> dict:
        """Returns the indexed content of the document
        {
            "docno": "92302",
            "content": "lorem ipsum"
        }
        """
        pass

    @staticmethod
    @abstractmethod
    def get_raw(docno: str) -> dict:
        """Returns the raw document content
        {
            "docno": "92302",
            "raw": "lorem ipsum"
        }
        """
        pass
