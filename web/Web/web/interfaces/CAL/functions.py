from config.settings.base import CAL_SERVER_IP
from config.settings.base import CAL_SERVER_PORT
import json
import logging
import urllib.parse

import httplib2
import requests

from web.CAL.exceptions import CALServerError
from web.CAL.exceptions import CALServerSessionNotFoundError

logger = logging.getLogger(__name__)


def send_judgment(session, doc_id, rel, next_batch_size=5):
    """
    Send judgment to CAL server for training
    :param session:
    :param doc_id:
    :param rel:
    :param next_batch_size:
    :return:
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/judge"

    body = {'session_id': str(session),
            'doc_id': doc_id,
            'rel': rel}
    body = urllib.parse.urlencode(body)
    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT),
                              body=body,
                              headers={'Content-Type': 'application/json; charset=UTF-8'},
                              method="POST")

    if resp and resp['status'] == '200':
        content = json.loads(content.decode('utf-8'))
        return content['docs'], content['top-terms']
    else:
        raise CALServerError(resp['status'])


def check_docid_exists(session, doc_id):
    """
    Checks if a docid exists in collection
    :param session:
    :param doc_id:
    :return:
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/docid_exists?"

    parameters = {
        'session_id': str(session),
        'doc_id': doc_id}
    parameters = urllib.parse.urlencode(parameters)
    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT) + parameters,
                              method="GET")

    if resp and resp['status'] == '200':
        content = json.loads(content.decode('utf-8'))
        return content["exists"]
    else:
        raise CALServerError(resp['status'])


def add_session(session, seed_query, mode):
    """
    Adds session to CAL backend server
    :param session:
    :param seed_query
    :param mode
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/begin"

    body = {'session_id': str(session),
            'seed_query': seed_query,
            'judgments_per_iteration': 1,
            'async': True,
            'mode': mode}
    post_body = '&'.join('%s=%s' % (k, v) for k, v in body.items())

    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT),
                              body=post_body,
                              headers={'Content-Type': 'application/json; charset=UTF-8'},
                              method="POST")
    if resp and resp['status'] != '200':
        return False
    else:
        raise CALServerError(resp['status'])


def delete_session(session):
    """
    Removes session from CAL memory
    :param session:
    :return:
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/delete_session"

    body = {'session_id': str(session)}
    body = urllib.parse.urlencode(body)
    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT),
                              body=body,
                              headers={'Content-Type': 'application/json; charset=UTF-8'},
                              method="DELETE")

    if resp and resp['status'] == '200':
        return True
    else:
        raise CALServerError(resp['status'])


def get_documents(session, num_docs):
    """
    :param session: current session
    :param num_docs: number of documents to return
    :return: return JSON list of documents_ids to judge
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/get_docs?"

    parameters = {'session_id': str(session),
                  'max_count': num_docs}
    parameters = urllib.parse.urlencode(parameters)
    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT) + parameters,
                              method="GET")

    if resp and resp['status'] == '200':
        content = json.loads(content.decode('utf-8'))

        return content['docs'], content['top-terms']
    elif resp and resp['status'] == '404':
        raise CALServerSessionNotFoundError(resp['status'])
    else:
        raise CALServerError(resp['status'])


def restore_session(session_id, seed_query, seed_documents, session_strategy):
    """
    :param session_id:
    :param seed_query:
    :param seed_documents: Must be a queryset of the the model Judgment
    :param session_strategy:
    :return: request response
    """
    url = f"http://{CAL_SERVER_IP}:{CAL_SERVER_PORT}/CAL/begin"
    seed_docs = ','.join([d.doc_id + ':' + str(d.relevance) for d in seed_documents])
    print(seed_docs)
    print(seed_documents)

    data = 'session_id={}&seed_query={}&seed_judgments={}&mode={}'.format(
        session_id, seed_query, seed_docs, session_strategy)

    return requests.post(url, data=data)


def get_scal_info(session):
    """
    :param session: current session
    :return: return JSON object
    """
    h = httplib2.Http()
    url = "http://{}:{}/CAL/get_stratum_info?"

    parameters = {'session_id': str(session)}
    parameters = urllib.parse.urlencode(parameters)
    resp, content = h.request(url.format(CAL_SERVER_IP,
                                         CAL_SERVER_PORT) + parameters,
                              method="GET")
    if resp and resp['status'] == '200':
        content = json.loads(content.decode('utf-8'))
        if not content:
            return None
        else:
            return content['info']
    else:
        raise CALServerError(resp['status'])
