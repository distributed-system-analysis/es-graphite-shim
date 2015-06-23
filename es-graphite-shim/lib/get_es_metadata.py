import os
import json
from elasticsearch import client
from collections import defaultdict
from time import ctime

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# def get_fieldnames(es_conn, _field, _indices, result=defaultdict(list), doc_type=''):
def get_fieldnames(es_conn, _field, _indices, result=[], doc_type=''):
    """
    Runs Elasticsearch aggs for all fieldnames 
    as per value of _field
    """
    _aggs = { 'aggs': {'aggs_custom': {'terms': {'field': _field,
                                                 'order':
                                                 {'_term':'asc'},
                                                 'size': 10000 }}},
              'fields': [] }

    N = 50
    for _ix in range(0, len(_indices), N):
        print("[%s] - %d Indices being processed starting from %d" % (ctime(), N, _ix))
        current = []
        res = es_conn.search(doc_type=doc_type, body=_aggs,
                             search_type='count', index=_indices[_ix:_ix+N])

        # convert '.' separated values to '_' separated
        # because grafana treats '.' separated as metric name
        for item in res['aggregations']['aggs_custom']['buckets']:
            current.append('_'.join(item['key'].split('.')))

        result.extend(list(set(current)))

    return result


def issue_mappings_query(es_conn, doc_type):
    """
    Issue actual ES query to retrieve mappings
    """
    es_client = client.IndicesClient(es_conn)    
    _MAPPINGS = es_client.get_mapping(doc_type=doc_type)
    d = {}
    for i in list(_MAPPINGS.values()):
        d.update(i)
    
    return d


def get_open_indices_list(es_conn, prefix, doc_type):
    """
    Query list of all open indices and return list.
    """
    es_client = client.ClusterClient(es_conn)
    response = es_client.state(ignore_unavailable=True, metric="metadata")
    resp = [ix for ix in list(response['metadata']['indices'].keys()) \
                    if '%s.%s' % (prefix, doc_type) in ix]
    return resp


def get_mappings(es_conn, doc_type, _fresh=False):
    """
    Return one single mapping combined by combining 
    individual index mappings to form a big updated list.

    This returns a saved mapping from a json file or it
    may issue an actual query to ES based on value of _fresh
    """
    if _fresh == 'True':
        return issue_mappings_query(es_conn, doc_type)
    else:
        try:
            f = open(os.path.join(BASE_DIR,
                                  'lib/mappings/es_mappings.json'), 'rb')
            _MAPPINGS = json.loads(f.read().decode('utf-8'))
            f.close()
            return _MAPPINGS
        except:
            print("[%s] - WARNING: es_mappings.json doesn't exist; falling back to issuing es query"\
                  % (ctime()))
            return issue_mappings_query(es_conn, doc_type)
