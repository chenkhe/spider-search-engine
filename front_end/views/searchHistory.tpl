<!DOCTYPE html>
<html>
<head>
	<link rel="stylesheet" type="text/css" href="css/common.css">
</head>
<body>
	</br>
	<a href={{homeURL}}>Back to home</a></br></br>
	<img src="images/spider.jpg" width="50" height="50" /></br>
	<table width="300" id="searchHistory">
		<caption>Search History</caption>
		<tr><th>Word</th><th>Count</th></tr>
		%if searchHistory != None:
			%for entry in searchHistory:
				%word, count = entry[0], entry[1]
				<tr><td>{{word}}</td><td>{{count}}</td></tr>
			%end
		%end
	</table>
</body>
</html>