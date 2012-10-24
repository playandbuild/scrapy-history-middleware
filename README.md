scrapy-history-middleware
=========================

The history middleware is designed to create a permanent record of the
raw requests and responses generated as scrapy crawls the web.

It also functions as a drop-in replacement for the builtin scrapy
httpcache middleware
(`scrapy.contrib.downloadermiddleware.httpcache.HttpCacheMiddleware`). For
example:

```python

    DOWNLOADER_MIDDLEWARES = {
        'history.middleware.HistoryMiddleware': 901 # Right after HttpCacheMiddleware
    }

    EPOCH = True
    HISTORY = {
        'STORE_IF'   : 'history.logic.StoreAlways',
        'RETRIEVE_IF': 'history.logic.RetrieveAlways',
        'BACKEND'    : 'history.storage.S3CacheStorage',
        'S3_ACCESS_KEY': {{ AWS_ACCESS_KEY_ID }},
        'S3_SECRET_KEY': {{ AWS_SECRET_ACCESS_KEY }},
        'S3_BUCKET'    : {{ S3_BUCKET }},
        'USE_PROXY'  : True,
    }
```

Will store and retrieve responses exactly as you expect. However, even
if multiple developers are working on the same spider, the spidered
website will only ever see one request (so long as they all use the
same S3 bucket).

Scrapy introduced the `DbmCacheStorage` backend in version 0.13. In
principle this is capable of interfacing with S3, but the history
middleware is still necessary as it provides versioning capability.

## Requirements

To run the middleware:

  * `parsedatetime`
  * `boto`. If using the S3 storage backend.

Testing:

  * `nose`
  * `nose-cov`
  * `coverage`

## Config

The history middleware is designed to play well with the httpcache
middleware. As such, the default logic modules use
`HTTPCACHE_IGNORE_MISSING`, `HTTPCACHE_IGNORE_SCHEMES`, and
`HTTPCACHE_IGNORE_HTTP_CODES`, and responses will not be stored if
they are flagged as having returned from the cache storage.

The middleware also requires two other settings: `EPOCH` and
`HISTORY`.

### Epoch

Usage: EPOCH can either be defined in `settings.py`,
`local_settings.py`, or on the command line, eg.,:

```bash
    $ scrapy crawl {{ spider }} --set="EPOCH=yesterday"
```

Note that scrapy will choose the value in local_settings.py over the
command line.

Possible values:

  * `True`: The middleware will always try to retrieve the most
    recently stored version of a url, subject to the logic in
    `RETRIEVE_IF`.

  * `False` (default): The middleware won't ever try to retrieve
    stored responses.

  * `{{ string }}`: The middleware will attempt to generate a datetime
    using the heuristics of the
    [parsedatetime](http://code.google.com/p/parsedatetime/)
    module. The retrieved response will either be newer than `EPOCH`,
    or the most recently stored response.

### History

A dictionary containing:

  * `STORE_IF`: (default `history.logic.StoreAlways`) Path to a
    callable that accepts the current spider, request, and response as
    arguments and returns `True` if the response should be stored, or
    `False` otherwise.

  * `RETRIEVE_IF`: (default `history.logic.RetrieveNever`) Path to a
    callable that accepts the current spider and request as arguments
    and returns `True` if the response should be retrieved from the
    storage backend, or `False` otherwise.

  * `BACKEND`: (default `history.storage.S3CacheStorage`) The storage
    backend.

  * `S3_ACCESS_KEY`: Required if using `S3CacheStorage`.

  * `S3_BUCKET_KEY`: Required if using `S3CacheStorage`.

  * `S3_BUCKET`: Required if using `S3CacheStorage`.
