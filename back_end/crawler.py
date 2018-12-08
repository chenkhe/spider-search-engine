import urlparse
import numpy as np
from boto.dynamodb2.table import Table
from crawler_thread import *
import threading
from operator import itemgetter

""" Main entry point of crawler. Crawl the web! """

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    # Lock for seen. seen is a member variable in crawler, which contains a list
    # of doc id that has been visited by crawler_thread.
    seen_lock = threading.Lock()
    # Lock for doc id counter and doc id cache(lexicon) and lexicon reverse access
    doc_id_lock = threading.Lock()
    # Lock for word id counter, word id cache and doc index access
    word_id_lock = threading.Lock()
    # Lock during read/write into inverted index
    inverted_index_lock = threading.Lock()

    # Atomic counter for doc_id and word_id. Shared by crawler_threads.
    doc_id_counter = 0
    word_id_counter = 0

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = []
        self._doc_id_cache = {}

        # word id cache is also called lexicon, dict with mapping (word, wordId)
        self._word_id_cache = {}

        # Initialize lexicon reverse, dict with mapping (wordId, word)
        # document_index with mapping (documentId, url) and inverted_index with mapping (wordId, documentId).
        self.lexicon_reverse = {}
        self.document_index = {}
        self.inverted_index = {}
        self.resolved_inverted_index = {}

        # For pageRank. outgoing_links is a list of mapping (docId, docId of outgoing links)
        self.outgoing_links = []

        # For pageRank. page_scores is a dict with mapping (docId, page rank score)
        self.page_scores = {}

        # If the crawler_thread has processed a doc, add the doc id into seen. This now becomes
        # a shared data structure as multiple threads (crawler_thread) process docs concurrently.
        self.seen = set()

        # Get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

    def _mock_insert_document(self, url):
        """Increment doc id counter. To ensure this operation is ATOMIC, LOCK HAS BEEN
        ACQUIRED by its caller self.document_id"""
        crawler.doc_id_counter += 1
        return crawler.doc_id_counter

    def _mock_insert_word(self, word):
        """Increment word id counter. To ensure this operation is ATOMIC, LOCK HAS BEEN
        ACQUIRED by its caller self.word_id"""
        crawler.word_id_counter += 1
        return crawler.word_id_counter

    def word_id(self, word):
        """Get the word id of some specific word."""
        # Multiple threads might insert same word into lexicon concurrently. Need critical section.
        try:
            crawler.word_id_lock.acquire()
            # _word_id_cache has a mapping of (word, wordId)
            if word in self._word_id_cache:
                word_id = self._word_id_cache[word]
            else:
                word_id = self._mock_insert_word(word)
                self._word_id_cache[word] = word_id
                # Store (wordId, word) mapping into lexicon reverse
                self.lexicon_reverse[word_id] = word
        finally:
            crawler.word_id_lock.release()
        return word_id

    def document_id(self, url):
        """Get the document id for some url."""
        # Multiple threads might insert same url into doc index concurrently. Need critical section.
        try:
            crawler.doc_id_lock.acquire()
            if url in self._doc_id_cache:
                doc_id = self._doc_id_cache[url]
            else:
                # Increment doc id counter and return the next doc id.
                doc_id = self._mock_insert_document(url)
                self._doc_id_cache[url] = doc_id
                # Store (documentId, url) into document_index
                self.document_index[doc_id] = url
        finally:
            crawler.doc_id_lock.release()
        return doc_id

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add an outgoing link to be passed in into pageRank algorithm.
            :param from_doc_id document id that has outgoing link
            :param to_doc_id document id that corresponds to one of the outgoing links for from_doc_id """
        self.outgoing_links.append((from_doc_id, to_doc_id))

    def getWord(self, wordId):
        """ Get word string from word id through lexicon reverse. """
        try:
            return self.lexicon_reverse[wordId]
        except Exception as e:
            raise

    def getUrl(self, docId):
        """ Get url string from doc id through document index. """
        try:
            return self.document_index[docId]
        except Exception as e:
            raise

    def _add_words_to_document(self, curr_words, curr_doc_id):
        """ Store (wordId, docId) and (word, url) into inverted_index and resolved_inverted_index respectively. """
        self.store_word_url(curr_words, curr_doc_id)

    def store_word_url(self, curr_words, curr_doc_id):
        """ Store (wordId, docId) and (word, url) into inverted_index and resolved_inverted_index respectively. """

        # Enter critical section. inverted_index is shared by crawler_threads and concurrent updates could happen.
        # Lock the inverted and resolved inverted index before reading/writing inverted index.
        try:
            crawler.inverted_index_lock.acquire()
            for wordId, font in curr_words:
                # Put wordId and corresponding list of docId into inverted_index
                if wordId in self.inverted_index:
                    docs = self.inverted_index[wordId]
                    docs.add(curr_doc_id)
                    self.inverted_index[wordId] = docs
                else:
                    self.inverted_index[wordId] = {curr_doc_id}

                # Put word and corresponding list of urls into resolved_inverted_index
                word = self.getWord(wordId)
                url = self.getUrl(curr_doc_id)
                if word in self.resolved_inverted_index:
                    urls = self.resolved_inverted_index[word]
                    urls.add(url)
                    self.resolved_inverted_index[word] = urls
                else:
                    self.resolved_inverted_index[word] = {url}

        finally:
            crawler.inverted_index_lock.release()

    def checkDocVisitedAndUpdate(self, doc_id):
        """ Check if the doc_id has been visited/processed by any of crawler_threads. Add doc_id to seen
         if not so."""
        # Whether doc is visited or not.
        visited = False
        # seen is a shared data structure and need acquire lock to enter critical section.
        try:
            crawler.seen_lock.acquire()
            if doc_id not in self.seen:
                self.seen.add(doc_id)
            else:  # The doc has been visited previously.
                visited = True
        finally:
            crawler.seen_lock.release()

        return visited

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def crawl(self, depth=2, timeout=3):
        """Crawl the web concurrently!"""
        # Keep track of the number of active threads before we start forking many crawler_threads (worker threads)
        activeThreadCountBeforeForkingWorkerThreads = threading.activeCount()

        # Python has no do-while loop, so use True and break at the end of while loop.
        while True:
            # If url queue is not empty, pop a url and fork a crawler_thread to process the url.
            if len(self._url_queue) != 0:
                url, depth_ = self._url_queue.pop()
                crawler_thread(self, url, depth_, depth, timeout).start()

            # If all crawler_threads (worker threads) has died off and no more urls are left in url queue to be processed,
            # then our work is done!
            if len(self._url_queue) == 0 and threading.activeCount() == activeThreadCountBeforeForkingWorkerThreads:
                break

    def get_inverted_index(self):
        """ Return inverted_index which has mapping of (wordId, set of document_ids). """
        return self.inverted_index

    def get_resolved_inverted_index(self):
        """Return inverted_index in the form of (word_string, set of url strings) """
        return self.resolved_inverted_index

    def get_document_index(self):
        return self.document_index

    def get_lexicon_reverse(self):
        return self.lexicon_reverse

    def get_word_id_cache(self):
        return self._word_id_cache

    def printInfo(self):
        """ Print inverted index, lexicon reverse, doc and resolved inverted index """
        print "Inverted index (wordId, set of document ids): " + str(bot.get_inverted_index())
        print "Lexicon (wordId, word): " + str(bot.get_word_id_cache())
        print "Document index (docId, url): " + str(bot.get_document_index())
        print "Resolved inverted index (word, list of urls): " + str(bot.get_resolved_inverted_index())

    def page_rank(self, links, num_iterations=20, initial_pr=1.0):
        """ Page rank algorithm downloaded from lab3 handout """
        page_rank = defaultdict(lambda: float(initial_pr))
        num_outgoing_links = defaultdict(float)
        incoming_link_sets = defaultdict(set)
        incoming_links = defaultdict(lambda: np.array([]))
        damping_factor = 0.85

        # collect the number of outbound links and the set of all incoming documents
        # for every document
        for (from_id, to_id) in links:
            num_outgoing_links[int(from_id)] += 1.0
            incoming_link_sets[to_id].add(int(from_id))

        # convert each set of incoming links into a numpy array
        for doc_id in incoming_link_sets:
            incoming_links[doc_id] = np.array([from_doc_id for from_doc_id in incoming_link_sets[doc_id]])

        num_documents = float(len(num_outgoing_links))
        lead = (1.0 - damping_factor) / num_documents
        partial_PR = np.vectorize(lambda doc_id: page_rank[doc_id] / num_outgoing_links[doc_id])

        for _ in xrange(num_iterations):
            for doc_id in num_outgoing_links:
                tail = 0.0
                if len(incoming_links[doc_id]):
                    tail = damping_factor * partial_PR(incoming_links[doc_id]).sum()
                page_rank[doc_id] = lead + tail

        return page_rank

    def persist(self):
        """ Persist data retrieved by crawler into DynamoDB """
        self.persistHelper(self._word_id_cache, "lexicon", "word", "wordId")
        self.persistHelper(self.inverted_index, "inverted_index")
        self.persistHelper(self.document_index, "document_index")
        self.persistHelper(dict(self.page_scores), "page_rank")

        # Bonus feature. What front end side of search engine really needs is that given a word, return a list of urls
        # such that the word exists in each url. The urls in the list is sorted from the highest page rank to lowest.
        # So the code below populates a table with (word, sorted urls) mapping into DynamoDB.
        # So now the front end side of search engine only needs to query the table below to display search results to
        # users. lexicon, inverted_index and page_rank are no longer needed. For the purpose of lab however, those tables
        # are still persisted into DynamoDB.
        self.persistHelper(self.get_word_sorted_urls(), "word_sorted_urls", "word", "sorted_urls")

    def persistHelper(self, dict, tableName, hashKey="id", attr="value"):
        """ Loop each entry in dictionary and write into dynamoDB table. By default,
        the table has hashkey with name 'id' and an attribute with name 'value'. This
        assumes table has a single hash key and attribute only.
        :param tableName table name in DynamoDB """

        # Connect to DynamoDB table with tableName.
        table = Table(tableName)
        for key, value in dict.iteritems():
            table.put_item(data={hashKey: str(key),
                                 attr: str(value)})

    def get_word_sorted_urls(self):
        """
            Return (word, sorted urls) dictionary. sorted urls mean a list of urls in which
            the word exists in all urls in the list, and the urls are sorted from the highest
            page rank to lowest. To do that,
            1. word -> wordId through lexicon
            2. wordId -> docIds through inverted index
            3. docIds -> url page ranks -> sorted docIds through page scores
            4. sorted docIds -> sorted urls through document index

            Note: docId in sorted docIds are sorted from the highest page rank doc to lowest.
        """
        word_sorted_urls = {}
        for word in self._word_id_cache:
            word_id = self._word_id_cache[word]
            doc_ids = self.inverted_index[word_id]
            sorted_reverse_doc_ids = self.get_sorted_reverse_doc_ids(doc_ids)
            sorted_urls = self.get_sorted_reverse_urls(sorted_reverse_doc_ids)
            sorted_urls_string = ', '.join(sorted_urls)
            word_sorted_urls[word] = sorted_urls_string
        return word_sorted_urls

    def get_sorted_reverse_doc_ids(self, doc_ids):
        """ Given doc_ids, return sorted doc ids such that each docId
        in sorted docIds are sorted from the highest page rank doc to lowest """
        doc_id_to_ranks = []
        for id in doc_ids:
            doc_id_to_ranks.append((id, dict(self.page_scores)[id]))
        doc_id_to_ranks = sorted(doc_id_to_ranks, key=itemgetter(1), reverse=True)
        sorted_reverse_doc_ids = [str(doc_id_to_rank[0]) for doc_id_to_rank in doc_id_to_ranks]
        return sorted_reverse_doc_ids

    def get_sorted_reverse_urls(self, sorted_reverse_doc_ids):
        """ Map each doc id into its respective url, while preserving the order of the list. """
        sorted_reverse_urls = []
        for doc_id in sorted_reverse_doc_ids:
            sorted_reverse_urls.append(self.document_index[int(doc_id)])
        return sorted_reverse_urls

if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    # Crawl the web concurrently! Took 2.3 seconds in my local machine, which is
    # much faster than 9.2 seconds! 9.2 seconds is for single threaded crawl in my
    # local machine.
    bot.crawl(depth=1)
    # Give scores for all web pages crawled!
    bot.page_scores = bot.page_rank(bot.outgoing_links)
    # Persist data retrieved from crawler into DynamoDB.
    bot.persist()