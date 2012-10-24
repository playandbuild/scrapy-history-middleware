=============================
Downloader History Middleware
=============================

The history middleware is designed to create a permanent record of the
raw requests and responses generated as scrapy crawls the web.

It also functions as a drop-in replacement for the builtin scrapy
httpcache middleware. For example::

    DOWNLOADER_MIDDLEWARES = {
        'dacrawl.middleware.history.HistoryMiddleware': 901 # Right after HttpCacheMiddleware
    }

    EPOCH = True
    HISTORY = {
        'STORE_IF'   : 'dacrawl.middleware.history.logic.StoreAlways',
        'RETRIEVE_IF': 'dacrawl.middleware.history.logic.RetrieveAlways',
        'BACKEND'    : 'dacrawl.middleware.history.storage.S3CacheStorage',
        'S3_ACCESS_KEY': {{ AWS_ACCESS_KEY_ID }},
        'S3_SECRET_KEY': {{ AWS_SECRET_ACCESS_KEY }},
        'S3_BUCKET'    : {{ S3_BUCKET }}
    }

Will store and retrieve responses exactly as you expect. However, even
if multiple developers are working on the same spider, the spidered
website will only ever see one request (so long as they all use the
same S3 bucket).

Scrapy introduced the DbmCacheStorage backend in version 0.13. In
principle this is capable of interfacing with S3, but the history
middleware is still necessary as it provides versioning capability.

Requirements
============

* ``parsedatetime``
* ``boto``. If using the S3 storage backend.

Config
======

The history middleware is designed to play well with the httpcache
middleware. As such, the default logic modules use
``HTTPCACHE_IGNORE_MISSING``, ``HTTPCACHE_IGNORE_SCHEMES``, and
``HTTPCACHE_IGNORE_HTTP_CODES``, and responses will not be stored if
they are flagged as having returned from the cache storage.

EPOCH
-----

Usage: EPOCH can either be defined in local_settings.py, or on the
command line, eg.,::

    $ scrapy crawl {{ spider }} --set="EPOCH=yesterday"

Note that scrapy will choose the value in local_settings.py over the
command line.

:``True``:
    The middleware will always try to retrieve the most recently
    stored version of a url, subject to the logic in retrieve_if.

:``False``:
    The middleware won't ever try to retrieve stored responses.

:``{{ string }}``:
    The middleware will attempt to generate a datetime using the
    heuristics of the parsedatetime_ module. The retrieved response
    will either be newer than EPOCH, or the most recently stored
    response.

.. _parsedatetime: http://code.google.com/p/parsedatetime/

    Default: ``False``

HISTORY
-------

A dictionary.

:``STORE_IF``:
    Path to a callable that accepts the current spider, request, and
    response as arguments and returns True if the response should be
    stored, or False otherwise.

    DEFAULT: ``StoreAlways``.

:``RETRIEVE_IF``:
    Path to a callable that accepts the current spider and request as
    arguments and returns True if the response should be retrieved
    from the storage backend, or False otherwise.

    DEFAULT: ``RetrieveNever``.

:``BACKEND``:
    The storage backend.

    DEFAULT: ``S3CacheStorage``.

:``S3_ACCESS_KEY``:
    Required if using ``S3CacheStorage``.

:``S3_BUCKET_KEY``:
    Required if using ``S3CacheStorage``.

:``S3_BUCKET``:
    Required if using ``S3CacheStorage``.
