from bottle import route, run, request, static_file, redirect, app, error, template
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import httplib2
from beaker.middleware import SessionMiddleware
from paginatedResult import PaginatedResult
from dynamodb_dao import dynamodb_dao
from gevent import monkey; monkey.patch_all()
from math import ceil
from autocomplete import *
from random import shuffle

#---------- constant ------------
CLIENT_ID = "828532786093-328qecd5csi5k7ta0kndb59jsh11t64r.apps.googleusercontent.com"
CLIENT_SECRET = "FMep0-MF9hd6awtWPtW7YSAS"
SCOPE = 'https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email'

MAX_HISTORY_SIZE = 10
MAX_AUTOCOMPLETE_SIZE = 10
PAGE_SIZE = 2  #items per page
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 3000,
    'session.data_dir': './data',
    'session.auto': True
}

''' Use on AWS '''
REDIRECT_URI = "http://ec2-54-172-65-181.compute-1.amazonaws.com/redirect"
HOME_URL = "http://ec2-54-172-65-181.compute-1.amazonaws.com"
''' For local use '''
#HOME_URL = "http://localhost:8080"
#REDIRECT_URI = HOME_URL + "/redirect"


# reassign home url to the value passed in as argument
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print "Usage: ", sys.argv[0], "home_url"
        sys.exit(2)
        
    HOME_URL  = sys.argv[1]

#---------- Global object instance or data structure that shoud be kept alive when server is running ------------
AllSearchHistory = {}
dao = dynamodb_dao()
trie = getAutoCompleteTrie()

#---------- Functions for render page ------------
@error(code=404)
@error(code=405)
def renderErrorPage(error=None):
	'''Display error page caused by error code 404 and 405'''
	return template('error')

@route('/viewSearchHistory')
def renderSearchHistory():
	'''Pull search history and render it on search history page'''

	session = request.environ['beaker.session']
	searchHistory = None
	if 'logged_in' in session and session['logged_in'] == True and session['user_email'] in AllSearchHistory:
		searchHistory = AllSearchHistory[session['user_email']]
	return template('searchHistory', searchHistory=searchHistory, homeURL=HOME_URL)

@route('/resultPage=<page>')
def renderResultByPage(page):
	'''render matching URLs according to last seach keywords and page intended'''

	session = request.environ['beaker.session']
	if 'keywords' not in session or session['keywords'] == None:
		return renderErrorPage()

	keywords = session['keywords']
	searchWord = keywords.split(" ")[0]

	if 'logged_in' not in session or session['logged_in'] == False:
		username = "Anonymous"
		isLoggedIn = False
	else:
		username = session['user_email']
		isLoggedIn = True

	results = getResultsFromDB(searchWord)
	# for testing
	# results = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"] * 10
	if results == None or len(results) < 1:
		return renderErrorPage()

	# if page number in url is out of range
	# jump back to page 1
	if int(page) not in range(1, int(ceil(len(results) / float(PAGE_SIZE))) + 1):
		return renderErrorPage()

	paginatedResult = getPaginatedResult(results, page=int(page))
	return template('home', keywords=keywords, username=username, isLoggedIn=isLoggedIn, \
		paginatedResult=paginatedResult, homeURL=HOME_URL)

@route('/', method='GET')
def renderHomePage():
	'''Render page depending on the get request'''

	# Get the session object from the environ
	session = request.environ['beaker.session']

	# Check if user is logged in
	if 'logged_in' in session and session['logged_in'] == True:
		isLoggedIn = True
	else:
		session['logged_in'] = False
		isLoggedIn = False

	# Get username
	if 'user_email' in session and isLoggedIn == True:
		username = session['user_email']
	else:
		username = "Anonymous"

	# Get keywords
	keywords = request.GET.get("keywords")
	if keywords != None:
		keywords = keywords.strip()

	results = ""
	history = ""
	searchHistory = []
	paginatedResult = None

	if isLoggedIn == True and username in AllSearchHistory:
		searchHistory = AllSearchHistory[username]

	# Get result if user actually search for something
	if keywords != None and keywords != "":
		# Take first word of keywords only for Lab 3
		searchWord = keywords.split(" ")[0]
		session['keywords'] = keywords
		wordCount = [(searchWord, 1)]
		if isLoggedIn == True:
			AllSearchHistory[username] = updateSearchHistory(searchHistory, wordCount)
			searchHistory = AllSearchHistory[username]

		# call DynamoDB API, provide word, get back a string consisting URLs delimited by comma
		urlList = getResultsFromDB(searchWord)
		# for testing
		# urlList = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"] * 10
		paginatedResult = getPaginatedResult(urlList)

	return template('home', keywords=keywords, username=username, isLoggedIn=isLoggedIn, \
		paginatedResult=paginatedResult, homeURL=HOME_URL)

#---------- Functions for user action e.g. login, login etc, ------------
@route('/logout', 'GET')
def logoutUser():
	'''Logout user and do some cleanup on the session'''

	# Get the session object from the environ
	session = request.environ['beaker.session']
	# Check if user is logged in
	if 'logged_in' in session and session['logged_in'] == True:
		session['logged_in'] = False
		session['keywords'] = None

	redirect(str(HOME_URL))

@route('/login', 'GET')
def loginUser():
	'''Get authorize uri to start the login flow based on information in client secret json'''

	flow = flow_from_clientsecrets("./data/client_secrets.json", scope=SCOPE, redirect_uri=REDIRECT_URI)
	uri = flow.step1_get_authorize_url()
	redirect(str(uri))

@route('/redirect')
def completeAuthenticationFlow():
	'''Complete the authentication flows and then redirect back to home page'''

	# authenticate user
	code = request.query.get('code', '')
	flow = OAuth2WebServerFlow(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope=SCOPE, redirect_uri=REDIRECT_URI)
	credentials = flow.step2_exchange(code)
	token = credentials.id_token['sub']
	http = httplib2.Http()
	http = credentials.authorize(http)
	# Get user email
	users_service = build('oauth2', 'v2', http=http)
	users_document = users_service.userinfo().get().execute()
	user_email = users_document['email']
	# update user session
	session = request.environ.get('beaker.session')
	session['user_email'] = user_email
	session['logged_in'] = True
	session.save()

	# go back to home page of application
	redirect(str(HOME_URL))

#---------- Functions that simple return data from server, image, css, js etc. ------------
@route('/images/<filename:re:.*\.jpg>', method='GET')
def getImage(filename):
	'''Return image with matching file name to the browser'''
	return static_file(filename, root='./images/', mimetype='image/jpg')

@route('/css/<filename:re:.*\.css>', method='GET')
def getCSS(filename):
	'''Return css with matching file name to the browser'''
	return static_file(filename, root='./css/')

@route('/js/<filename:re:.*\.js>', method='GET')
def getJavascript(filename):
	'''Return javascript with matching file name to the browser'''
	return static_file(filename, root='./js/')

@route('/autocomplete=')
@route('/autocomplete=<word>')
def getAutoCompleteData(word=""):
	'''Get matching autocomplete words from trie and return it as dictionary'''

	if word == "":
		return
	else:
		results = trie.search(word)
		resultsCount = len(results)
		#convert into dictionary form as dictionary is supported
		#for Bottle to convert it into JSON compatible string to ajax callback
		if resultsCount < 1:
			return
		elif resultsCount >= MAX_AUTOCOMPLETE_SIZE:
			#shuffle(results)
			retval = dict(zip(range(0, MAX_AUTOCOMPLETE_SIZE), results[0:MAX_AUTOCOMPLETE_SIZE]))
		else:
			retval = dict(zip(range(0, len(results)), results))
		return retval

#---------- Functions that return an object for server use e.g. paginatedResult instance, dao instance etc. ------------
def getPaginatedResult(results, page=1):
	'''Convert results into a paginated result object instance'''

	if results == None or len(results) < 1:
		return None
	else:
		return PaginatedResult(currentPage=page, pageSize=PAGE_SIZE, homeURL=HOME_URL, results=results)

def getResultsFromDB(searchWord):
	'''Get resuls from DB and return a list of URLs'''

	global dao
	resultString = ""
	try:
		resultString = dao.get_sorted_urls(searchWord)
	except:
		print "Error in getting list"
	
	if resultString == "":
		return None
	
	urlList = resultString.split(", ")

	return urlList

def getWordCount(keywords):
	'''
	This function compute word count of each words in the keywords
	Return a dictionary containing word as key and word count as value 
	'''
	parsedKeywords = keywords.split();
	#wordCount = {}
	wordCount = []
	for word in parsedKeywords:
		if any(str(word) in entry for entry in wordCount):
			entryIndex = [entry[0] for entry in wordCount].index(word)
			wordCount[entryIndex] = (wordCount[entryIndex][0], wordCount[entryIndex][1] + 1)
		else:
			wordCount.append((word, 1))

	return wordCount

#---------- Functions that updates global data structure stored in memory ------------
def updateSearchHistory(searchHistory, wordCount):
	'''
	This function update global search history according to
	word count in new keywords
	Only top 10 search are kept in the history
	Priority is given to most recent search word when the history needs to be trimmed
	'''

	newHistoryList = []
	for entry in wordCount:
		word = entry[0]
		count = entry[1]
		# increment count in history if exist
		if any(str(word) in history for history in searchHistory):
			# find the location of the history to be updated
			historyIndex = [history[0] for history in searchHistory].index(word)
			updatedHistory = (searchHistory[historyIndex][0], searchHistory[historyIndex][1] + count)
			# delete the old entry of history and append updated one to end of list
			del searchHistory[historyIndex]
			searchHistory.append(updatedHistory)
		else:
			# append to new history list, later add all items in this list into search history
			newHistoryList.append((word, count))

	# trim new history if there are too much new entries
	while len(newHistoryList) > MAX_HISTORY_SIZE:
		newHistoryList.pop()

	# trim history first if the list will be too big after added new history
	newLength = len(newHistoryList) + len(searchHistory)
	if newLength > MAX_HISTORY_SIZE:
		trimSearchHistory(searchHistory, newLength - MAX_HISTORY_SIZE)

	searchHistory += newHistoryList
	return searchHistory
	
def trimSearchHistory(searchHistory, numberOfEntry):
	'''
	This function trim search history depending on how many entries to be trimmed
	Entry with min value is removed while trimming
	First entry encountered is removed if there is a tie
	'''

	while numberOfEntry>0:
		entryToRemove = min(searchHistory, key = lambda history:history[1])
		searchHistory.remove(entryToRemove)
		numberOfEntry -= 1

#---------- start server instance ------------
app = SessionMiddleware(app(), session_opts)
''' Use on AWS '''
run(app=app, host='0.0.0.0', port=80, debug=True, server='gevent')
''' For local use '''
#run(app=app, host='localhost', port=8080, debug=True)
