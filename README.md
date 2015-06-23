es-graphite-shim
================

Shim for mocking Graphite instance through ElasticSearch, for Grafana.

**INSTALLATION**

Refer to __INSTALL-NOTES__ for help on installing this script.

Or you could just build the Dockerfile included here and fire the container.
Instructions for building and starting the container, are included in the Dockerfile.
Before that, make sure you have copied ```conf/local_settings_example.py``` into
```conf/local_settings.py``` and edited the params as required. Help on editing those
parameters is given under __INSTALL-NOTES__

- Make sure you supply the params to config.js in grafana accordingly. Refer below:
```js
..
// Graphite & Elasticsearch example setup

datasources: {
  graphite: {
  type: 'graphite',
  url: "<URL of shim>",
  timezone: 'Asia/Kolkata',
 },
elasticsearch: {
  type: 'elasticsearch',
  url: "<ES Instance where dashboard metadata is to be stored>",
  index: 'grafana-dash',
  grafanaDB: true,
 }
},

..
```

The __timezone__ option under __datasources.graphite__ has to be mentioned
in case the timezone offsets differ. This normally has to be same as the
one mentioned under __local_settings.py__ (__TIME_ZONE__ = '')

**USAGE**

To run this in development mode, just like any other
django project would be executed.

``` $ python manage.py runserver ```

Or, you might deploy this on a production server. For this,
refer to the sample apache based deployment help guide included
within the source code, in a file called INSTALL-NOTES and sample
apache config under conf/graphite_shim.conf.example

Following that, on homepage, you will see some sample links.

There are two categories of the shim API, as follows:

1) __Render Query Type__:

   ```/render/?target={{metric_path}}&from={{epoch_from}}&until={{epoch_until}}&format=json```

  - Here, the metric_path is a DOT (.) separated path (similar to graphite) that specifies
    the path of the query metrics, as per the hierarchy. This may be:

    ```metric1.sub_metric1.sub_sub_metric1. <and so on>```

  - The ```from=``` and ```until=``` fields specify the time durations between which the query
    is to be performed.

  - ```format=json``` ensures the response is JSON formatted.

  - Please note, for demonstration purposes, a sample query has been provided in the homepage
    HTML file. The params provided to it, come from within the views.py file under
    ```homepage(request)```. You could modify the query path and epoch intervals accordingly.

2) __Metric Search Query Type__:

   ```/metrics/find?query=*```

   - Here, when * is given, all the parent nodes in the metric path hierarchy are displayed as
     a result, along with information like, whether its a leaf node or not.

**LICENSE**

Refer to the file 'LICENSE'.
