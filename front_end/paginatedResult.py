from math import ceil

class PaginatedResult(object):

    def __init__(self, currentPage, pageSize, homeURL, results):
        self.currentPage = currentPage
        self.pageSize = pageSize
        self.totalCount = len(results)
        ''' Depreciated
        self.resultCache = resultCache
        self.cacheSize = cacheSize
        self.cacheStartPage = cacheStartPage
        '''
        currentIndex = (currentPage - 1) * pageSize
        if self.hasNext:
            self.results = results[currentIndex:currentIndex + pageSize]
        else:
            # either is at the last page or there is only 1 page in total
            self.results = results[currentIndex:]

        self.homeURL = homeURL

    @property
    def totalPages(self):
        return int(ceil(self.totalCount / float(self.pageSize)))

    @property
    def hasPrev(self):
        return self.currentPage > 1

    @property
    def hasNext(self):
        return self.currentPage < self.totalPages

    def getPageIterator(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.totalPages + 1):
            if num <= left_edge or \
                (num > self.currentPage - left_current - 1 and \
                num < self.currentPage + right_current) or \
                num > self.totalPages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def getResult(self):
        return self.results

    def getURLByPage(self, page):
        return "resultPage=" + str(page)