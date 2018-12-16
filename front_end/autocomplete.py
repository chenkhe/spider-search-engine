#!/usr/bin/env python
import sys

DICTIONARY_FILE = "dictionary.txt"

class Node:

    def __init__(self):
        self.next = {}  # Initialize an empty hash (python dictionary)
        self.word_marker = False
        # There can be words, Hot and Hottest. When search is performed, usually state transition upto leaf node is performed and characters are printed.
        # Then in this case, only Hottest will be printed. Hot is an intermediate state. In order to mark t as a state where word is to be print, a word_marker is used

    def add_item(self, string):
        ''' Method to add a string to the Trie data structure'''

        if len(string) == 0:
            self.word_marker = True
            return

        key = string[0]  # Extract first character
        string = string[1:]  # Create a string by removing first character

        # If the key character exists in the hash, call next pointing node's add_item() with remaining string as argument
        if key in self.next:
            self.next[key].add_item(string)
        # Else create an empty node. Insert the key character to hash and point it to newly created node. Call add_item() in new node with remaining string.
        else:
            node = Node()
            self.next[key] = node
            node.add_item(string)

    def dfs(self, sofar=None):
        '''Perform Depth First Search Traversal'''
        results = []
        # When hash of the current node is empty, that means it is a leaf node.
        # Hence print sofar (sofar is a string containing the path as character sequences through which state transition occured)
        if self.next.keys() == []:
            # print "Match:",sofar
            results.append(sofar)
            return results

        if self.word_marker == True:
            # print "Match:",sofar
            results.append(sofar)

        # Recursively call dfs for all the nodes pointed by keys in the hash
        for key in self.next.keys():
            newResults = self.next[key].dfs(sofar + key)
            if newResults != None:
                results = results + newResults

        return results

    def search(self, string, sofar=""):
        '''Perform auto completion search and print the autocomplete results'''
        results = []
        # Make state transition based on the input characters.
        # When the input characters becomes exhaused, perform dfs() so that the trie gets traversed upto leaves and print the state characters
        if len(string) > 0:
            key = string[0]
            string = string[1:]
            if key in self.next:
                sofar = sofar + key
                newResults = self.next[key].search(string, sofar)
                if newResults != None:
                    results = results + newResults

            else:
                print
                "No match"
        else:
            if self.word_marker == True:
                # print "Match:",sofar
                results.append(sofar)

            for key in self.next.keys():
                newResults = self.next[key].dfs(sofar + key)
                if newResults != None:
                    results = results + newResults

        return results


def getAutoCompleteTrie():
    '''Parse the input dictionary file and build the trie data structure'''
    fd = open(DICTIONARY_FILE)

    root = Node()
    line = fd.readline().strip('\r\n')  # Remove newline characters \r\n

    while line != '':
        root.add_item(line)
        line = fd.readline().strip('\r\n')

    return root

# MAIN FUNCTION THAT TEST IF THE TRIE BUILDS CORRECTLY STANDALONE

# if __name__ == '__main__':
#
#     # build the Trie from dictionary.txt
#     root = getAutoCompleteTrie()
#
#     # TO-DO: Please change the user's keyword in input variable
#     input="hi"
#
#     # stores all the relevant words in dictionary.txt to results
#     results = root.search(input)
#     print(results)
#     print(len(results))