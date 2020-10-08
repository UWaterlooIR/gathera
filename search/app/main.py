import os
from timeit import default_timer as timer

from fastapi import FastAPI
from fastapi import HTTPException
from pyserini import index
from pyserini.search import SimpleSearcher

INDEX_PATH = os.environ['ANSERINI_INDEXI_PATH']

# Initialize pyserini searcher and index reader
searcher = SimpleSearcher(INDEX_PATH)
index_reader = index.IndexReader(INDEX_PATH)

# Configure BM25 parameters
searcher.set_bm25(0.9, 0.4)

app = FastAPI()


@app.get("/")
def read_root():
    return {"index_path": INDEX_PATH}


@app.get("/search/")
def search(query: str, size: int = 100):
    start = timer()
    hits = searcher.search(query, k=size)
    end = timer()
    total_time = end - start
    hits_clean = []

    for i in range(len(hits)):
        content = index_reader.doc_contents(hits[i].docid)
        h = {
            "rank": i + 1,
            "docno": hits[i].docid,
            "score": hits[i].score,
            "title": content[:55],
            "snippet": content[:350]
        }
        hits_clean.append(h)

    return {
        "query": query,
        "total_matches": len(hits),
        "size": size,
        "total_time": total_time,
        "hits": hits_clean
    }


@app.get("/docs/{docno}/content")
def get_content(docno: str):
    content = index_reader.doc_contents(docno)
    if content is None:
        raise HTTPException(status_code=404, detail="Doc not found")
    return {
        "docno": docno,
        "content": content
    }


@app.get("/docs/{docno}/raw")
def get_content(docno: str):
    raw = index_reader.doc_raw(docno)
    if raw is None:
        raise HTTPException(status_code=404, detail="Doc not found")
    return {
        "docno": docno,
        "raw": raw
    }
