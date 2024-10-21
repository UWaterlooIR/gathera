from config.settings.base import DOCUMENTS_URL
from config.settings.base import PARA_URL

import httplib2
import requests
import re

try:
    # For c speedups
    from simplejson import loads
except ImportError:
    from json import loads


def get_date(content):
    for line in content.split('\n'):
        if line.strip()[:4] == "Sent":
            try:
                return line.split(':', 1)[1].strip()
            except:
                pass
    return ""


def cleanhtml(raw_html):
    CLEANR = re.compile('<.*?>') 
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext

def get_subject(content):
    for line in content.split('\n'):
        if line.strip()[1:6] == "title":
            return cleanhtml(line.strip())
    return ""


def remove_initial_non_alphanumeric(content):
    i=0
    if content == None:
        return content
    while i < len(content):
        if content[i:i+2] == '\n':
            i += 3
        elif content[i:i+4] == '<br>':
            i += 5
        elif content[i] == " ":
            i += 1
        else:
            return content[i:]



def get_documents(doc_ids, query=None, top_terms=None, orig_para_id=None):
    """
    :param query:
    :param doc_ids: the ids of documents to return
    :return: documents content
    """
    result = []
    h = httplib2.Http()
    for idx, doc_id in enumerate(doc_ids):
        url = '{}/{}'.format(DOCUMENTS_URL, doc_id)
        resp, content = h.request(url,
                                  method="GET")
        content = remove_initial_non_alphanumeric(content.decode('utf-8', 'ignore'))
        date = get_date(content)
        title = remove_initial_non_alphanumeric(get_subject(content))
        if len(content) == 0:
            if not title or len(title) == 0:
                title = '<i class="text-warning">The document title is empty</i>'
            content = '<i class="text-warning">The document content is empty</i>'
        else:
            if not title or len(title) == 0:
                title = content[:32]
        print(title)
        document = {
            'doc_id': doc_id,
            'title': title,
            'content': content,
            'date': date,
            'top_terms': top_terms.get(doc_id if orig_para_id is None else "{}.{}".format(doc_id, orig_para_id[idx]), None) if top_terms else None,
            'ok': resp.status == 200
        }
        result.append(document)

    return result


def get_documents_with_snippet(doc_ids, query=None, top_terms=None):
    h = httplib2.Http()
    url = "{}/{}"
    doc_ids_unique = []
    doc_ids_set = set()
    for doc_id in doc_ids:
        if doc_id['doc_id'] not in doc_ids_set:
            doc_ids_set.add(doc_id['doc_id'])
            doc_ids_unique.append(doc_id)

    doc_ids = doc_ids_unique

    result = get_documents([doc['doc_id'] for doc in doc_ids], query, top_terms, [doc['para_id'] for doc in doc_ids if 'para_id' in doc])
    for doc_para_id, doc in zip(doc_ids, result):
        if 'para_id' not in doc_para_id:
            doc['snippet'] = u''
            continue
        try:
            para_id = doc_para_id['doc_id'] + '.' + doc_para_id['para_id']
            resp, content = h.request(url.format(PARA_URL, para_id),
                                      method="GET")
            doc['snippet'] = content.decode('utf-8', 'ignore')
        except:
            doc['snippet'] = u''
    return result
