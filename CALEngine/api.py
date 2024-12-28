""" Python bindings for bmi_fcgi
"""

import base64
import requests
import json
from json import JSONDecodeError

class SessionExistsException(Exception):
    pass

class SessionNotFoundException(Exception):
    pass

class DocNotFoundException(Exception):
    pass

class InvalidJudgmentException(Exception):
    pass

# URL = 'http://scspc538.cs.uwaterloo.ca:9002/CAL'
URL = 'http://localhost:9001/CAL'

def set_url(url):
    """ Set API endpoint
    """
    global URL
    while url[-1] == '/':
        url = url[:-1]
    URL = url

def setup(dataset_name='atome4', seed_document_id="", seed_document_content="", is_complete=False):
    """
        Setup CAL using one document as input

        Args:
            dataset_name(str): used to construct the paths of doc and para features. The default is 'athome4'
            seed_document_id: the document id 
            seed_document_content: the document content
            is_complete: boolean to mark the end of post requests
        
        Returns:
            json response
    """
    doc_features = '{}_sample.bin'.format(dataset_name)
    para_features = '{}_para_sample.bin'.format(dataset_name)

    data = {
        'doc_features': doc_features,
        'para_features': para_features,
        'document_id': seed_document_id,
        'is_complete': is_complete,
        'document_content': base64.b64encode(seed_document_content).decode('ascii'),
    }
    data = '&'.join(['%s=%s' % (k,v) for k,v in data.items()])

    resp = requests.post(URL+'/setup', data=data).json()
    return resp


def bulk_setup(dataset_name='atome4', seed_documents=[], delimiter='<|CAL_DOC_END|>'):
    """
        Setup CAL using a list of documents as input (up to 340 documents max from athome4)

        Args:
            seed_documents([(str, str), ]): List of tuples of document ids and their corresponding contents
            delimiter(str): used to parse document contents. The default is '<|CAL_DOC_END|>'
            dataset_name(str): used to construct the paths of doc and para features. The default is 'athome4'
        
        Returns:
            json response
    """
    doc_features = '{}_sample.bin'.format(dataset_name)
    para_features = '{}_para_sample.bin'.format(dataset_name)

    data = {
        'doc_features': doc_features,
        'para_features': para_features,
        'delimiter': delimiter,
    }
    if len(seed_documents) > 0:
        data['seed_documents'] = delimiter.join(
            ['%s<|CAL_SEP|>%s' % (doc_id, base64.b64encode(doc_content).decode('ascii')) for doc_id, doc_content in seed_documents])

    data = '&'.join(['%s=%s' % (k,v) for k,v in data.items()])
    resp = requests.post(URL+'/bulk_setup', data=data).json()
    return resp


def begin_session(session_id, seed_query, async_mode=False, mode="doc", seed_documents=[], judgments_per_iteration=1):
    """ Creates a bmi session

    Args:
        session_id (str): unique session id
        seed_query (str): seed query string
        async_mode (bool): If set to True, the server retrains in background whenever possible
        mode (str): For example, "para" or "doc"
        seed_documents ([(str, int), ]): List of tuples containing document_id (str) and its relevance (int)
        judgments_per_iteration (int): Batch size; -1 for default bmi

    Return:
        None

    Throws:
        SessionExistsException
    """

    data = {
        'session_id': str(session_id),
        'seed_query': seed_query,
        'async_mode': str(async_mode).lower(),
        'mode': mode,
        'judgments_per_iteration': str(judgments_per_iteration)
    }
    if len(seed_documents) > 0:
        data['seed_judgments'] = ','.join(['%s:%d' % (doc_id, rel) for doc_id, rel in seed_documents])

    data = '&'.join(['%s=%s' % (k,v) for k,v in data.items()])
    r = requests.post(URL+'/begin', data=data)
    resp = r.json()
    if resp.get('error', '') == 'session already exists':
        raise SessionExistsException("Session %s already exists" % session_id)


def get_docs(session_id, max_count=1):
    """ Get documents to judge

    Args:
        session_id (str): unique session id
        max_count (int): maximum number of doc_ids to fetch

    Returns:
        document ids ([str,]): A list of string document ids

    Throws:
        SessionNotFoundException
    """
    data = '&'.join([
        'session_id=%s' % str(session_id),
        'max_count=%d' % max_count
    ])
    resp = requests.get(URL+'/get_docs?'+data).json()

    if resp.get('error', '') == 'session not found':
        raise SessionNotFoundException('Session %s not found' % session_id)

    return resp['docs']


def get_stratum_info(session_id):
    """ Get

    Args:
        session_id (str): unique session id

    Returns:

    Throws:
        SessionNotFoundException
    """
    data = '&'.join([
        'session_id=%s' % str(session_id),
    ])
    resp = requests.get(URL+'/get_stratum_info?'+data).json()

    if resp.get('error', '') == 'session not found':
        raise SessionNotFoundException('Session %s not found' % session_id)

    return resp

def judge(session_id, doc_id, rel):
    """ Judge a document
    Args:
        session_id (str): unique session id
        doc_id (str): document id
        rel (int): Relevance judgment 1 or -1

    Returns:
        None

    Throws:
        SessionNotFoundException, DocNotFoundException, InvalidJudgmentException
    """
    if rel > 0:
        rel = 1
    else:
        rel = -1

    data = '&'.join([
        'session_id=%s' % str(session_id),
        'doc_id=%s' % doc_id,
        'rel=%d' % rel
    ])
    resp = requests.post(URL + '/judge', data=data).json()

    if resp.get('error', '') == 'session not found':
        raise SessionNotFoundException('Session %s not found' % session_id)
    elif resp.get('error', '') == 'session not found':
        raise DocNotFoundException('Document %s not found' % doc_id)
    elif resp.get('error', '') == 'session not found':
        raise InvalidJudgmentException('Invalid judgment %d for doc %s' % (rel, doc_id))


def get_ranklist(session_id):
    """ Get the current ranklist

    Args:
        session_id (str): unique session id

    Returns:
        ranklist ([(str, float), ]): Ranked list of document ids

    Throws:
        SessionNotFoundException
    """
    data = '&'.join(['session_id=%s' % str(session_id)])
    resp = requests.get(URL+'/get_ranklist?'+data)

    try:
        if resp.json().get('error', '') == 'session not found':
            raise SessionNotFoundException('Session %s not found' % session_id)
    except JSONDecodeError:
        pass

    ranklist = []
    ret = json.loads(resp.text)
    for pair in ret["ranklist"].split(","):
        doc_id, score = pair.split(" ")
        ranklist.append((doc_id, float(score)))

    return ranklist


def delete_session(session_id):
    """ Delete a session

    Args:
        session_id (str): unique session id

    Returns:
        None

    Throws:
        SessionNotFoundException
    """

    data = '&'.join(['session_id=%s' % str(session_id)])
    resp = requests.delete(URL+'/delete_session', data=data).json()

    if resp.get('error', '') == 'session not found':
        print(SessionNotFoundException('Session %s not found' % session_id))
