from datetime import datetime, timedelta

from scrapy.conf import settings
from scrapy.utils.httpobj import urlparse_cached


class LogicBase(object):
    def __init__(self, settings=settings):
        self.ignore_missing = settings.getbool('HTTPCACHE_IGNORE_MISSING', False)
        self.ignore_schemes = settings.getlist('HTTPCACHE_IGNORE_SCHEMES', ['file'])
        self.ignore_http_codes = map(int, settings.getlist('HTTPCACHE_IGNORE_HTTP_CODES', []))

    def spider_opened(self, spider):
        pass

    def spider_closed(self, spider):
        pass

    def _cache_if(self, spider, request, response=None):
        """
        A request is cacheable if the URI scheme is not in
        HTTPCACHE_IGNORE_SCHEMES. By default:
            file:// - not cacheable
            http:// - cacheable

        A response is cacheable if the http response code is not in
        HTTPCACHE_IGNORE_HTTP_CODES. For example, we may choose to
        ignore 404.
        """
        cacheable_request = (
            urlparse_cached(request).scheme not in self.ignore_schemes )

        if (not response) or (not cacheable_request):
            # == if not (response and cacheable_request)
            return cacheable_request

        cacheable_response = (
            'cached'   not in response.flags and # from HttpCacheMiddleware
            'historic' not in response.flags and # from HistoryMiddleware
            response.status not in self.ignore_http_codes )

        return cacheable_request and cacheable_response

class RetrieveBase(LogicBase):
    def __call__(self, spider, request, response=None):
        if self._cache_if(spider, request):
            return self.retrieve_if(spider, request)
        else:
            return False

    def retrieve_if(self, spider, request):
        raise NotImplementedError("Please implement in your subclass.")

class StoreBase(LogicBase):
    def __call__(self, spider, request, response):
        if self._cache_if(spider, request, response):
            return self.store_if(spider, request, response)
        else:
            return False

    def store_if(self, spider, request, response):
        raise NotImplementedError("Please implement in your subclass.")


class RetrieveNever(RetrieveBase):
    """
    Never attempt to retrieve response from cache.
    """
    def retrieve_if(self, spider, request):
        return False

class RetrieveAlways(RetrieveBase):
    """
    Always attempt to retrieve response from.
    """
    def retrieve_if(self, spider, request):
        return True


class StoreNever(StoreBase):
    """
    Never attempt to store response in cache.
    """
    def store_if(self, spider, request, response):
        return False

class StoreAlways(StoreBase):
    """
    Always attempt to store response in cache.
    """
    def store_if(self, spider, request, response):
        return True

class StoreDaily(StoreBase):
    """
    Store response only if it is currently between midnight and 1am.
    """
    def store_if(self, spider, request, response):
        return datetime.now().hour == 0
