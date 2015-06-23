#!/usr/bin/python

import json
import re
from datetime import datetime, timedelta
from django.conf import settings
from collections import defaultdict
from time import ctime
#     from calendar import timegm
#     dt = datetime.strptime(tmp, "%Y-%m-%d %H:%M:%S")
#     return timegm(dt.utctimetuple())

def flatten_list(L):
    v = []
    [v.extend(x) for x in L]
    return v


def form_response(text='', _id='', leaf=0, context={}, expandable=1, allowChildren=1):
    """ 
    Returns Grafana readable response.
    """
    return { "leaf": leaf,
             "context": context,
             "text": text,
             "expandable": expandable,
             "id": _id,
             "allowChildren": allowChildren }


def iterate_mappings(query=None, idx=2, metrics=None):
    """
    Finds out metric paths iteratively 
    """
    path = query[:idx]
    while query[idx:]:
        _metric = query[idx:][0]
        try:
            metrics = metrics[_metric]['properties']
            path.append(_metric)
        except KeyError:
            if _metric == '*':
                # is a mass query
                tmp = list(metrics.keys())
                if 'properties' in metrics[tmp[0]]:
                    _leaf = 0
                    expandable = 1
                    allowChildren = 1
                else:
                    _leaf = 1
                    expandable = 0
                    allowChildren = 0
                metrics = tmp
                if idx == 2:
                    metrics.remove('_metadata')
                    metrics.remove('timestamp')
                return [_leaf, expandable, allowChildren, path, metrics]
            elif _metric in metrics:
                if len(query[idx:]) == 1:
                    # inference: query doesn't have a * at the end
                    _leaf = 1
                    expandable = 0
                    allowChildren = 0
                    return [_leaf, expandable, allowChildren, path, query]
                else:
                    return None
                # doesn't contain 'properties'
            else:
                # is invalid query
                return None
        idx += 1
        
    expandable = 1
    allowChildren = 1
    _leaf = 0
    return [_leaf, expandable, allowChildren, path, query]


def find_metrics(query):
    """
    API of graphite mocked: /metric/find?query= 
    """
    response = []    
    query = query.split('.')
    first_metric_list = settings._FIELDS

    if len(query) == 1:
        if query[0] == '*':
            # return all first_metric_list
            for name in first_metric_list:
                response.append(form_response(text=name, _id=name))
        else:
            # if no '*' in query, validate fieldname
            if query[0] in first_metric_list:
                response.append(form_response(text=query[0], _id=query[0]))
            else:
                return json.dumps(response)

    elif len(query) >= 2:
        mappings = settings._MAPPINGS
        doc_types = list(mappings['mappings'].keys())
        assert query[0] in first_metric_list

        if len(query) == 2:
            if query[1] == '*':
                # TODO: filter query for fieldname specific docs
                for doc_type in doc_types:
                    response.append(form_response(text=doc_type,
                                                  _id=query[0] + '.' + doc_type))
            else:
                assert query[1] in doc_types
                response.append(form_response(text=query[1],
                                              _id=query[0] + '.' + query[1]))

        elif len(query) > 2:
            assert query[1] in doc_types
            metrics = mappings['mappings'][query[1]]['properties']
            result = iterate_mappings(query=query, metrics=metrics)
            if result:
                if result[-1] == query:
                    # query without * at the end
                    response.append(form_response(text=query[-1], _id='.'.join(query),
                                                  leaf=result[0], allowChildren=result[2],
                                                  expandable=result[1]))
                else:
                    # query with * at the end
                    for item in result[-1]:
                        response.append(form_response(text=item, _id='.'.join(result[-2]) + '.' + item,
                                                      leaf=result[0], allowChildren=result[2],
                                                      expandable=result[1]))
            else:
                # invalid query
                json.dumps(response)

    return json.dumps(response)


def restructure_query(pos=None, tmp=[], target=None, items=[]): 
    if tmp:
        for i in range(len(tmp)):
            k = []
            for current in items:
                curr = tmp[i][:]
                curr[pos] = current
                k.append(curr)
            tmp[i] = k
        tmp = flatten_list(tmp)
    else:
        for current in items:
            _target = target[:] # copy target
            _target[pos] = current
            tmp.append(_target)
            
    return tmp


def query_es(_type=None, _COUNT=10, fieldname=None, _fields=[], _from="-2d", _until="now"):
    _fields.append("_timestamp")

    if _until == 'now':
        timelt = datetime.now()
        try:
            timegt = datetime.utcfromtimestamp(float(_from)) 
        except:
            if 'd' in _from:
                timegt = timelt + timedelta(days=int(_from.strip('d')))
            elif 'h' in _from:
                timegt = timelt + timedelta(hours=int(_from.strip('h')))
            elif 'min' in _from:
                timegt = timelt + timedelta(minutes=int(_from.strip('min')))
            else:
                return []
    else:
        timelt = datetime.utcfromtimestamp(float(_until)) 
        timegt = datetime.utcfromtimestamp(float(_from))

    indexes = defaultdict(int)
    ltday = timelt.strftime("%Y%m%d")
    indexes[ltday] = 1
    ts = timegt
    oneday = timedelta(days=1)
    while ts < timelt:
        indexes[ts.strftime("%Y%m%d")] += 1
        ts += oneday

    suffix_list = [suffix for suffix in list(indexes.keys())]
    suffix_list.sort(reverse=True)
    index_list = ["%s.%s-%s" % (settings.INDEX_PREFIX, settings.DOC_TYPE, suffix) for suffix in suffix_list]

    _body = {
        "size": 2**8,
        "query": {
            "filtered": {
                "filter": {
                    "and": {
                        "filters": [
                            {
                                "range": {
                                    "_timestamp": {
                                        "gt": timegt.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "lt": timelt.strftime("%Y-%m-%dT%H:%M:%S")
                                    },
                                    "execution": "fielddata",
                                    "_cache": "false"
                                }
                            },
                            {
                                "term": {
                                    settings.FIELD: fieldname,
                                    "_cache": "false"
                                }
                            }
                        ],
                        "_cache": "false"
                    }
                }
            }
        }
    }

    print("[%s] - Query Metadata: %s" % \
          (ctime(), _body))
    _body['fields'] = _fields
    res = settings.ES.search(doc_type=_type, body=_body, index=index_list)
    _fields.remove("_timestamp")

    return [x['fields'] for x in res['hits']['hits']]


def build_query(_doc_type, _node, fields, response, _COUNT, _FROM, _UNTIL, target):
    res = query_es(_type=_doc_type, _COUNT=_COUNT,
                    fieldname=_node, _fields=list(fields),
                    _from=_FROM,
                    _until=_UNTIL)

    for _field in fields:
        if res:
            d = {
                "target" : '.'.join([_node,target[1],_field]),
                "datapoints" : []
            }

            for current in res:
                d['datapoints'].append([current[_field][0], float(current['_timestamp'])/1000])
    
            response.append(d)

    # else:
    #     _init = ( int(_UNTIL) - int(_FROM) ) / 60 / 2 + int(_FROM)
    #     for _tstamp in range(_init, _init + 60 * 20, 60):
    #         d['datapoints'].append([None, _tstamp])

    return response


def render_metrics(_TARGETS, _FROM, _UNTIL, _COUNT):
    """
    API of graphite mocked: /render/? 
    """
    response = []
    first_metric_list = settings._FIELDS
    mappings = settings._MAPPINGS
    doc_types = list(mappings['mappings'].keys())

    for target in _TARGETS:
        brace_items = re.findall(r'(\{.+?\})+', target)
        target = target.split('.')
        
        if brace_items:
            tmp = []
            for item in brace_items[::-1]:
                try:
                    pos = target.index(item)
                except:
                    break

                # remove { } and then split comma delimited query
                items = item[:-1][1:].split(',')
                tmp = restructure_query(pos=pos, tmp=tmp, target=target, items=items)
                fields = set(['.'.join(x[2:]) for x in tmp])

        else:
            fields = set(['.'.join(target[2:])])

        fields_list = list(fields)

        try:
            # check for multiple first_metric_list and doc_types
            _node_check = bool(re.findall(r'(\{.+?\})+', target[0]))
            _doc_type_check = bool(re.findall(r'(\{.+?\})+', target[1]))

            # validate doc_types
            if _doc_type_check:
                _types = target[1][:-1][1:].split(',')
            else:
                _types = [target[1]]
            _doc_types = set(doc_types) & set(_types)
            if not bool(_doc_types):
                continue

            # validate fields
            for _doc_type in _doc_types:
                metrics = mappings['mappings'][_doc_type]['properties']
                for _field in fields:
                    query = _field.split('.')
                    result = iterate_mappings(query=query, idx=0, metrics=metrics)
                    if not bool(result):
                        fields_list.remove(_field)
            if not bool(fields_list):
                continue

            # validate first_metric_list
            if _node_check:
                _nodes = target[0][:-1][1:].split(',')
            else:
                _nodes = [target[0]]
            _nodes = set(first_metric_list) & set(_nodes)
            _nodes = ['.'.join(_.split('_')) for _ in _nodes]
            if not bool(_nodes):
                continue

            # Trigger rendering
            for _node in _nodes:
                for _doc_type in _doc_types:
                    try:
                        response = build_query(_doc_type, _node, fields_list, response, _COUNT, _FROM, _UNTIL, target)
                    except:
                        continue

        except:
            continue
        
    return json.dumps(response)
