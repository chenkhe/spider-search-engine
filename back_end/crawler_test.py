from crawler import crawler

""" Unit tests for crawler """

def test_page_rank():
    """ Test correctness of page rank """

    # Create test crawler object.
    testCrawler = crawler(None, "")
    links = [(1,2), (2, 4), (4, 3), (3, 1), (3, 2)]
    expected_scores = {1: 0.15667918572028511, 2: 0.28985649358252741, 3: 0.2791899914185817, 4: 0.2838780195451483}
    if cmp(dict(testCrawler.page_rank(links)), expected_scores) == 0:
        return True
    else:
        print "Error in test_page_rank(): Page rank is not calculated correctly."
        return False

def test_store_word_url():
    """ Test populating inverted index and resolved inverted index. """

    # Create test crawler object.
    testCrawler = crawler(None, "")

    # Constants for test inputs.
    WORD_ID_1 = 1
    WORD_ID_2 = 2
    WORD_ID_3 = 3
    FONT_SIZE = 7
    WORD_1 = "word1"
    WORD_2 = "word2"
    WORD_3 = "word3"
    DOC_ID = 1001
    URL_1 = "url1"

    # Test inputs.
    # wordId to word font size tuples.
    wordsFonts = ((WORD_ID_1, FONT_SIZE), (WORD_ID_2, FONT_SIZE), (WORD_ID_3, FONT_SIZE))
    # wordId to word string mappings.
    lexicon_reverse = {WORD_ID_1: WORD_1, WORD_ID_2: WORD_2, WORD_ID_3: WORD_3}
    # docId to url string mapping.
    document_index = {DOC_ID: URL_1}

    # Set test inputs into test crawler object.
    testCrawler.lexicon_reverse = lexicon_reverse
    testCrawler.document_index = document_index

    # Test the function, which populates inverted index and resolved inverted index.
    testCrawler.store_word_url(wordsFonts, DOC_ID)

    # Expected outputs.
    expectedInvertedIndex = {WORD_ID_1: {DOC_ID}, WORD_ID_2: {DOC_ID}, WORD_ID_3: {DOC_ID}}
    expectedResolvedInvertedIndex = {WORD_1: {URL_1}, WORD_2: {URL_1}, WORD_3: {URL_1}}

    if cmp(testCrawler.inverted_index, expectedInvertedIndex) != 0:
        print "Error in test_store_word_url(): Inverted index is not populated correctly."
        return False

    if cmp(testCrawler.resolved_inverted_index, expectedResolvedInvertedIndex) != 0:
        print "Error in test_store_word_url(): Resolved inverted index is not populated correctly."
        return False

    return True


def test_word_id():
    """ Test populating lexicon. """
    # Create test crawler object.
    testCrawler = crawler(None, "")

    # Call the test function, which gets wordId from word and populate lexicon(word_id_cache) and lexicon reverse.
    actualWordId = testCrawler.word_id("word1")
    expectedWordId = 1

    # Compare wordId returned.
    if actualWordId != expectedWordId:
        print "Error in test_word_id(): wordId returned is not correct. WordId: " + str(actualWordId)
        return False

    # Compare lexicon (word id cache) in crawler.
    if cmp(testCrawler._word_id_cache, {"word1": 1}) != 0:
        print "Error in test_word_id(): lexicon is not populated correctly. Lexicon: " + str(testCrawler._word_id_cache)
        return False

    # Compare lexicon reverse in crawler.
    if cmp(testCrawler.lexicon_reverse, {1: "word1"}) != 0:
        print "Error in test_word_id(): lexicon reverse is not populated correctly. Lexicon: " + str(testCrawler.lexicon_reverse)
        return False

    return True


def test_document_id():
    """ Test populating document index. """

    # Create test crawler object.
    testCrawler = crawler(None, "")
    testCrawler.document_index = {}

    # Call the test function, which gets docId from url and populate document index.
    actualDocId = testCrawler.document_id("url1")
    expectedDocId = 1

    # Compare docId returned.
    if actualDocId != expectedDocId:
        print "Error in test_document_id(): docId returned is not correct. DocId: " + str(actualDocId)
        return False

    # Compare document index populated.
    if cmp(testCrawler.document_index, {1: "url1"}) != 0:
        print "Error in test_document_id(): document_index is not populated correctly. Document Index: " + str(
            testCrawler.document_index)
        return False

    return True

def test_word_sorted_urls():
    """ Test populating word to sorted urls dictionary. """
    testCrawler = crawler(None, "")
    testCrawler.word_id("word1")
    testCrawler.document_id("doc1")
    # doc_id and word_id should be 2 now because previous unit test calls word_id and document_id
    # before, which incrases the static word and doc id counter by 1.
    testCrawler.inverted_index[2] = {2}
    testCrawler.page_scores[2] = 0.1
    if cmp(testCrawler.get_word_sorted_urls(), {'word1': 'doc1'}) != 0:
        print "Error in test_word_sorted_urls(): word_sorted_url is not populated!"
        return False
    return True

# Run unit tests! If the test passed, it will show True. Otherwise, False. 
# Descriptive error messages will be provided for test cases that are not passing.
print "Test Results: "
print "test_page_rank: " + str(test_page_rank())
print "test_store_word_url: " + str(test_store_word_url())
print "test_word_id: " + str(test_word_id())
print "test_document_id: " + str(test_document_id())
print "test_word_sorted_urls: " + str(test_word_sorted_urls())