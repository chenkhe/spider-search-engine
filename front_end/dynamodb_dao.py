__author__ = 'kchen'

from boto.dynamodb2.table import Table
from boto.dynamodb2 import connect_to_region

AWS_ACCESS_KEY_ID = "AKIAJC72JGVOJMXAK3NQ"
AWS_SECRET_ACCESS_KEY = "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"

class dynamodb_dao(object):
    """ Data access object for Dynamo DB tables. """

    def __init__(self):
        """ Initialize the instance that connects to "word_sorted_urls" table in DynamoDB. """
        conn = connect_to_region("us-east-1", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.word_sorted_urls = Table("word_sorted_urls", connection=conn)

    def get_sorted_urls(self, word):
        """ Given a word, return a list of urls such that the word exists in each url. The urls in the list
         is sorted from the highest page rank to lowest."""
        # Took 0.22 seconds
        return self.word_sorted_urls.get_item(word=str(word))['sorted_urls']
