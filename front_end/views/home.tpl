%if keywords == None or keywords == "":
	%valueAttribute = ""
	%hideSpan = "hidden"
%else:
	%hideSpan = ""
	%valueAttribute = keywords
%end

<!DOCTYPE html>
<html>
<head>
	<link rel="stylesheet" type="text/css" href="css/common.css">
	<link rel="stylesheet" type="text/css" href="css/dropdown.css">
</head>
<body>
	<div style="text-align: right">
		%if isLoggedIn == True:
			%buttonValue = "Logout"
			%buttonAction = buttonValue.lower()
			<nav class="menu">
			<ul>
				<li class="menuItem dropDown">
					<a href="#">{{username}}</a>
					<ul>
						<li><a href="/viewSearchHistory">View search history</a></li>
						<li>
							<a href="#">
							<form action="{{buttonAction}}" method="get">
					    		<input style="margin:10px;" type="submit" value="{{buttonValue}}"/>
					    	</form>
					    	</a>
						</li>
					</ul>
				</li>
			</ul>
			</nav>
		%else:
			%buttonValue = "Login"
			<span style="margin-right: 20px; font: bold 15px sans-serif">{{username}}</span>
			%buttonAction = buttonValue.lower()
	    	<form action="{{buttonAction}}" method="get">
	    		<input style="margin:10px;" type="submit" value="{{buttonValue}}"/>
	    	</form>
		%end
		
	</div>
	</br>
	<div style="clear: both;">
	<img src="images/spider.jpg" width="50" height="50" /><div id="searchEngineName">Spider Search</div></br>
	<form action="/" method="get">
		<input id="keywords" name="keywords" type="text" value="{{valueAttribute}}" size="50" oninput="textChange()" list="autoCompleteData" autocomplete="off"/></br></br>
		<input value="Crawl Web" type="submit"/></br></br>
	</form>
	</div>
	<span {{hideSpan}}><strong>Search for</strong> <i>{{valueAttribute}}</i></span></br></br>
	<div class=pagination>
		%if defined('paginatedResult') and paginatedResult != None:
			%if paginatedResult.totalPages > 1:
				%if paginatedResult.hasPrev:
				  	%pageURL = paginatedResult.getURLByPage(paginatedResult.currentPage - 1)
				  	<a href={{pageURL}}>&laquo; Prev</a>
				%end
				%for page in paginatedResult.getPageIterator():
				  	%if page:
				    	%if page != paginatedResult.currentPage:
				      		%pageURL = paginatedResult.getURLByPage(page)
				      		<a href={{pageURL}}>{{page}}</a>
				    	%else:
				     		<strong>{{page}}</strong>
				    	%end
				  	%else:
				    	<span class=ellipsis>…</span>
				  	%end
				%end
				%if paginatedResult.hasNext:
				  	%pageURL = paginatedResult.getURLByPage(paginatedResult.currentPage + 1)
				  	<a href={{pageURL}}>Next &raquo;</a>
				%end
			%end
	</div>
	<div>
			<table id="searchResult">
				<caption>Search Result</caption>
				% resultNum = 1
				%for result in paginatedResult.getResult():
				  	<tr><td>Result {{resultNum}}</td><td><a href={{result}}>{{result}}</a></br></td></tr>
				  	%resultNum += 1
				%end
			</table>
		%else:
			%if keywords != None and keywords != "":
				No search result
			%end
		%end
	</div>
	<div id="autoCompleteDiv">
	
	</div>
	<script src="js/autocomplete.js"></script>
</body>
</html>