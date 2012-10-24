from datetime import datetime
from parsedatetime import parsedatetime, parsedatetime_consts

from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.conf import settings
from scrapy.stats import stats
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.utils.misc import load_object


class HistoryMiddleware(object):
    DATE_FORMAT = '%Y%m%d'

    def __init__(self, settings=settings):
        history = settings.get('HISTORY', None)
        if not history:
            raise NotConfigured()

        # EPOCH:
        #   == False: don't retrieve historical data
        #   == True : retrieve most recent version
        #   == datetime(): retrieve next version after datetime()
        self.epoch = self.parse_epoch(settings.get('EPOCH', False))

        self.retrieve_if = load_object(history.get(
            'RETRIEVE_IF', 'history.logic.RetrieveNever'))(settings)
        self.store_if = load_object(history.get(
            'STORE_IF', 'history.logic.StoreAlways'))(settings)
        self.storage = load_object(history.get(
            'BACKEND', 'history.storage.S3CacheStorage'))(settings)
        self.ignore_missing = settings.getbool('HTTPCACHE_IGNORE_MISSING')

        dispatcher.connect(self.spider_opened, signal=signals.spider_opened)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)

    def spider_opened(self, spider):
        self.storage.open_spider(spider)
        self.store_if.spider_opened(spider)
        self.retrieve_if.spider_opened(spider)

    def spider_closed(self, spider):
        self.storage.close_spider(spider)
        self.store_if.spider_closed(spider)
        self.retrieve_if.spider_closed(spider)

    def process_request(self, request, spider):
        """
        A request is approaching the Downloader.

        Decide if we would like to intercept the request and supply a
        response ourselves.
        """
        if self.epoch and self.retrieve_if(spider, request):
            request.meta['epoch'] = self.epoch
            response = self.storage.retrieve_response(spider, request)
            if response:
                response.flags.append('historic')
                return response
            elif self.ignore_missing:
                raise IgnoreRequest("Ignored; request not in history: %s" % request)

    def process_response(self, request, response, spider):
        """
        A response is leaving the Downloader. It was either retreived
        from the web or from another middleware.

        Decide if we would like to store it in the history.
        """
        if self.store_if(spider, request, response):
            self.storage.store_response(spider, request, response)
            stats.set_value('history/cached', True, spider=spider)

        return response

    def parse_epoch(self, epoch):
        """
        bool     => bool
        datetime => datetime
        str      => datetime
        """
        if isinstance(epoch, bool) or isinstance(epoch, datetime):
            return epoch
        elif epoch == 'True':
            return True
        elif epoch == 'False':
            return False

        try:
            return datetime.strptime(epoch, self.DATE_FORMAT)
        except ValueError:
            pass

        parser = parsedatetime.Calendar(parsedatetime_consts.Constants())
        time_tupple = parser.parse(epoch) # 'yesterday' => (time.struct_time, int)
        if not time_tupple[1]:
            raise NotConfigured('Could not parse epoch: %s' % epoch)
        time_struct = time_tupple[0]      #=> time.struct_time(tm_year=2012, tm_mon=4, tm_mday=7, tm_hour=22, tm_min=8, tm_sec=6, tm_wday=5, tm_yday=98, tm_isdst=-1)
        return datetime(*time_struct[:6]) #=> datetime.datetime(2012, 4, 7, 22, 8, 6)
