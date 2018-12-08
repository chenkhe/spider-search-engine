var xmlhttp;

if (window.XMLHttpRequest) {
	// code for IE7+, Firefox, Chrome, Opera, Safari
	xmlhttp=new XMLHttpRequest();
} 
else {
	// code for IE6, IE5
	xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
}


// This function get data from ajax request and then fill it into
// auto complete list
function getAutoCompleteData()
{
	output = "";
  	if (xmlhttp.readyState==4 && xmlhttp.status==200) {
    
		// get content from callback
		var jsonobj = JSON.parse(xmlhttp.responseText); 
		var output = xmlhttp.responseText;

		// create autocomplete data list
		output = "";
		output += '<datalist id="autoCompleteData">';
		for (i in jsonobj) {
			output += '<option value="' + jsonobj[i] + '">';
		}
		output += '</datalist>';
  	}
	document.getElementById("autoCompleteDiv").innerHTML = output;
}

function textChange() { 
	var keywords = document.getElementById("keywords").value;

	// the GetItems function will be triggered once the ajax
	// request is terminated.
	xmlhttp.onload = getAutoCompleteData;

	// send the request in an async way
	xmlhttp.open("GET", "/autocomplete=" + keywords, true);
	xmlhttp.send();
}