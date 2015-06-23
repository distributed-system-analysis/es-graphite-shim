from django.template import RequestContext
from django.http import HttpResponse,  HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt #csrf_protect
from django.shortcuts import render_to_response
from . import query_formatter as qf

def homepage(request):
    """
    Overview / Landing Page
    """
    return render_to_response('index.html',
                              { 'project_name' : 'Query Processor',
                                'title' : 'Query Middleware app',
                                'metric_path' : 'sample_metric.{param1,param2}',
                                'epoch_from' : 1411890859,
                                'epoch_until' : 1424890859,
                              })


def view_mapping(request):
    """
    List all available fields
    """
    return HttpResponse(qf.json.dumps(qf.settings._MAPPINGS),
                        content_type="application/json")


@csrf_exempt
def metrics_render(request):
    if request.method == 'POST':
        _TARGETS = request.POST.getlist('target', None)
        _FROM = request.POST.get('from', None)
        _UNTIL = request.POST.get('until', None)

        # _COUNT = request.POST.get('maxDataPoints', 10)
        # FIXME: limit count to 10 for now. Remove constraint
        # once caching and other optimization techniques are
        # included, so that ES instance doesn't get bombarded
        # every time maxDataPoints goes above 1000 or something
        _COUNT = 10

        _FORMAT = request.POST.get('format', None)

        if _TARGETS and _FROM and _UNTIL and (_FORMAT == 'json'):
            return HttpResponse(qf.render_metrics(_TARGETS,
                                               _FROM,
                                               _UNTIL,
                                               _COUNT),
                                content_type="application/json")
        else:
            return HttpResponse('[]', content_type="application/json")

    elif request.method == 'GET':
        _TARGETS = request.GET.getlist('target', None)
        _FROM = request.GET.get('from', None)
        _UNTIL = request.GET.get('until', None)

        # _COUNT = request.GET.get('maxDataPoints', 10)
        _COUNT = 10

        _FORMAT = request.GET.get('format', None)
        if _TARGETS and _FROM and _UNTIL and (_FORMAT == 'json'):
            return HttpResponse(qf.render_metrics(_TARGETS,
                                               _FROM,
                                               _UNTIL,
                                               _COUNT),
                                content_type="application/json")
        else:
            return HttpResponse('[]', content_type="application/json")

    else:
        return HttpResponseNotFound('<h1>Method Not Allowed</h1>')        

    
def metrics_find(request):
    """ 
    Query for metric names, for templates and drop down list selection 
    """
    if request.method == 'GET':
        try:
            query = request.GET.get('query', None)
            if query:
                return HttpResponse(qf.find_metrics(query), 
                                    content_type="application/json")
            else:
                return HttpResponse("Missing required parameter 'query'")
        except Exception as e:
            return HttpResponse('[]', content_type="application/json")

    else:
        return HttpResponseNotFound('<h1>Method Not Allowed</h1>')

    
def dashboard_find(request):
    """ 
    Query for metric names, for templates and drop down list selection 
    """
    # FIXME: understand this query, for proper response
    if request.method == 'GET':
        # query = request.GET.get('query', None)
        resp = { "dashboards": [ ] }
        return HttpResponse(qf.json.dumps(resp), content_type="application/json")

    else:
        return HttpResponseNotFound('<h1>Method Not Allowed</h1>')
