from django.db.models import Q
from web.judgment.models import Judgment


def join_judgments(documents, document_ids, user, session):
    """
    Adds the relevance judgment of the document to the document_values dict.
    If document has not been judged yet, `isJudged` will be False.
    :param user:
    :param session:
    :param documents:
    :param document_ids:
    :return: document_values with extra information about the document
    """
    judged_docs = Judgment.objects.filter(user=user,
                                          session=session,
                                          doc_id__in=document_ids,
                                          relevance__isnull=False)

    judged_docs = {j.doc_id: j for j in judged_docs}
    for hit in documents:
        is_judged = True if hit['docno'] in judged_docs else False

        if is_judged:
            judgment_object = judged_docs.get(hit['docno'])
            hit['rel'] = judgment_object.relevance
            hit['isJudged'] = is_judged
            hit['relevance_judgment'] = judgment_object.relevance
            hit['additional_judging_criteria'] = judgment_object.additional_judging_criteria

    return documents


def padder(doc_ids):
    """
    Pads zeros to ids to be length of 7
    :param doc_ids: list of document ids
    :return: doc ids padded with 0 to be length of 7.
    """

    for idx, doc_id in enumerate(doc_ids):
        doc_id = doc_id.zfill(7)
        doc_ids[idx] = doc_id

    return doc_ids
