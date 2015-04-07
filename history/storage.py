from datetime import datetime
import boto
import pickle

from scrapy import log
from scrapy.conf import settings
from scrapy.utils.request import request_fingerprint
from scrapy.responsetypes import responsetypes


class S3CacheStorage(object):

    def __init__(self, settings=settings):
        history = settings.get('HISTORY')

        # Required settings
        self.S3_ACCESS_KEY   = history['S3_ACCESS_KEY']
        self.S3_SECRET_KEY   = history['S3_SECRET_KEY']
        self.S3_CACHE_BUCKET = history['S3_BUCKET']

        # Optional settings
        self.use_proxy = history.get('USE_PROXY', True)

    def _get_key(self, spider, request):
        key = request_fingerprint(request)
        return '%s/%s' % (spider.name, key)

    def open_spider(self, spider):
        self.s3_connection = boto.connect_s3(self.S3_ACCESS_KEY, self.S3_SECRET_KEY)
        self.s3_connection.use_proxy = self.use_proxy
        self.s3_bucket = self.s3_connection.get_bucket(self.S3_CACHE_BUCKET, validate=False)
        #self.versioning = self.s3_bucket.get_versioning_status() #=> {} or {'Versioning': 'Enabled'}

    def close_spider(self, spider):
        self.s3_connection.close()

    def _get_s3_key(self, key, epoch):
        """
        Return key with timestamp >= epoch.

        If epoch is not a datetime then just return the first key.

        The versions of a key in s3 are stored according to the time
        they were added. Thus the first result of element in
        s3_bucket.list_versions() is the most recent.

        s3_key.name: 0805...
               version_id  last_modified
               X72xb...    2012-04-17T02:25:37.000Z
               EFTqO...    2012-04-17T02:05:38.000Z
               zQtzi...    2012-04-16T23:01:53.000Z
               null        2012-04-14T11:47:16.000Z *

               * versioning was not enabled at this point
        """
        # list_versions returns an iterator interface; build an actual
        # iterator
        s3_keys = iter(self.s3_bucket.list_versions(prefix=key))

        # Since we assume the keys are returned in order of
        # modification the first key is the most recent result
        first_key = next(s3_keys, None)

        # We can only do version checks if we have a datetime to
        # compare with
        if not isinstance(epoch, datetime):
            return first_key

        # Try to find the first key that occurred after epoch but
        # iterating backward through time
        last_key = first_key
        for s3_key in s3_keys:
            if boto.utils.parse_ts(s3_key.last_modified) < epoch:
                return last_key
            else:
                last_key = s3_key

        # Nothing occured before epoch, therefore last_key is closest
        # to epoch
        return last_key

    def retrieve_response(self, spider, request):
        """
        Return response if present in cache, or None otherwise.
        """
        key = self._get_key(spider, request)

        epoch = request.meta.get('epoch') # guaranteed to be True or datetime
        s3_key = self._get_s3_key(key, epoch)

        if not s3_key:
            return

        log.msg('S3Storage (epoch => %s): retrieving response for %s.' % (epoch, request.url))
        try:
            data_string = s3_key.get_contents_as_string()
        except boto.exception.S3ResponseError as e:
            # See store_response for error descriptions
            raise e
        finally:
            s3_key.close()

        data = pickle.loads(data_string)

        metadata         = data['metadata']
        request_headers  = data['request_headers']
        request_body     = data['request_body']
        response_headers = data['response_headers']
        response_body    = data['response_body']

        url      = metadata['response_url']
        status   = metadata.get('status')
        Response = responsetypes.from_args(headers=response_headers, url=url)
        return Response(url=url, headers=response_headers, status=status, body=response_body)

    def store_response(self, spider, request, response):
        """
        Store the given response in the cache.
        """
        log.msg('S3Storage: storing response for %s.' % request.url)
        key = self._get_key(spider, request)

        log.msg('path: %s' % key)
        metadata = {
            'url': request.url,
            'method': request.method,
            'status': response.status,
            'response_url': response.url,
            #'timestamp': time(), # This will become the epoch
        }

        data = {
            'metadata'        : metadata,
            'request_headers' : request.headers,
            'request_body'    : request.body,
            'response_headers': response.headers,
            'response_body'   : response.body
        }
        data_string = pickle.dumps(data, 2)

        # With versioning enabled creating a new s3_key is not
        # necessary. We could just write over an old s3_key. However,
        # the cost to GET the old s3_key is higher than the cost to
        # simply regenerate it using self._get_key().
        s3_key = self.s3_bucket.new_key(key)

        try:
            #s3_key.update_metadata(metadata) #=> can't use this as need to cast to unicode
            for k, v in metadata.items():
                s3_key.set_metadata(k, unicode(v))
            s3_key.set_contents_from_string(data_string)
        except boto.exception.S3ResponseError as e:
            # http://docs.pythonboto.org/en/latest/ref/boto.html#module-boto.exception
            #   S3CopyError        : Error copying a key on S3.
            #   S3CreateError      : Error creating a bucket or key on S3.
            #   S3DataError        : Error receiving data from S3.
            #   S3PermissionsError : Permissions error when accessing a bucket or key on S3.
            #   S3ResponseError    : Error in response from S3.
            #if e.status == 404:   # Not found; probably the wrong bucket name
            #    log.msg('S3Storage: %s %s - %s' % (e.status, e.reason, e.body), log.ERROR)
            #elif e.status == 403: # Forbidden; probably incorrect credentials
            #    log.msg('S3Storage: %s %s - %s' % (e.status, e.reason, e.body), log.ERROR)
            raise e
        finally:
            s3_key.close()
