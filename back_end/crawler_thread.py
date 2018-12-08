from threading import Thread
import urllib2
from bs4 import BeautifulSoup
from bs4 import Tag
from collections import defaultdict
import re

""" Worker threads forked by crawler to process urls. """

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

class crawler_thread(Thread):
    """ Worker thread for crawler. Process a url and populate data into lexicon, inverted_index
    and document_index of crawler"""
    def __init__(self, crawler, url, depth_, depth, timeout, name="NoName"):
        Thread.__init__(self, name=name)
        self.crawler = crawler
        self.curr_url = url
        self.depth_ = depth_
        self.depth = depth
        self.timeout = timeout

        self._curr_depth = 0
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = [ ]

         # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame',
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset',
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

    def run(self):
        """ Process a url and populate data into lexicon, inverted_index
        and document_index of crawler """

        # The url is too deep, skip the url.. Work is done!
        if self.depth_ > self.depth:
            return

        # Get doc id corresponds to the url. Add a new entry into doc index if there is no entry.
        doc_id = self.crawler.document_id(self.curr_url)

        # Check if the doc_id has been visited/processed by any of crawler_threads. Add doc_id to seen if not so.
        if self.crawler.checkDocVisitedAndUpdate(doc_id):
            return

        # Process the document corresponds to the url
        socket = None
        try:
            socket = urllib2.urlopen(self.curr_url, timeout=self.timeout)
            soup = BeautifulSoup(socket.read())
            self._curr_depth = self.depth_ + 1
            self._curr_doc_id = doc_id
            # Traverse the document as deep as possible and add those newly discovered urls into url queue
            self._index_document(soup)
            # Store (wordId, docId) and (word, url) into inverted_index and resolved_inverted_index respectively.
            self.crawler._add_words_to_document(self._curr_words, self._curr_doc_id)
        except:
            pass
        finally:
            if socket:
                socket.close()

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)

                    continue

                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        pass

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self.crawler._fix_url(self.curr_url, attr(elem,"href"))

        # add the just found URL to the url queue
        self.crawler._url_queue.append((dest_url, self._curr_depth))

        # add a link entry into outgoing_links, which later be persisted into DynamoDB
        self.crawler.add_link(self._curr_doc_id, self.crawler.document_id(dest_url))

    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.crawler.word_id(word), self._font_size))

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it