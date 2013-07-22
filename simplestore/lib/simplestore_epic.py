#!/usr/bin/env python

import httplib2
#import socks
from simplejson import loads as jsonloads 
from simplejson import dumps as jsondumps
from xml.dom import minidom

from invenio.config import CFG_EPIC_USERNAME
from invenio.config import CFG_EPIC_PASSWORD
from invenio.config import CFG_EPIC_BASEURL
from invenio.config import CFG_EPIC_PREFIX
# Hardwire in the following two elements of the credentials file: is this correct?
#    "accept_format": "application/json",
#    "debug" : "False"


import uuid
import sys

"""
httplib2
download from http://code.google.com/p/httplib2
python setup.py install

simplejson
download from http://pypi.python.org/pypi/simplejson/
python setup.py install

ubuntu: apt-get install python-httplib2 python-simplejson
"""



def _debugMsg(debug, method, msg):
    """Internal: Print a debug message if debug is enabled."""
    if debug: 
        print "[",method,"]",msg

def createHandle(location,checksum=None,suffix=''):
    """Create a new handle for a file.

    Parameters:
    #prefix: URI to the resource, or the prefix if suffix is not ''. - NOT NEEDED?
    location: The location (URL) of the file.
    checksum: Optional parameter, store the checksum of the file as well.
    suffix: The suffix of the handle. Default: ''.
    Returns the URI of the new handle, None if an error occurred.

    """
    debug = True

    username = CFG_EPIC_USERNAME
    password = CFG_EPIC_PASSWORD
    baseurl = CFG_EPIC_BASEURL
    prefix = CFG_EPIC_PREFIX

    # Hardwire these just for the moment
    proxy = 'wwwcache.rl.ac.uk'
    proxyPort = 8080
    
    username = str(username)
    
    #http = httplib2.Http(proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, proxy, proxyPort), disable_ssl_certificate_validation=True)
#    http = httplib2.Http(proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, proxy, proxyPort))
    http = httplib2.Http()
    #r,c = http.request("http://www.bbc.co.uk")
    #print str(r)
    #print str(c)
    http.add_credentials(username, password)

    _debugMsg(debug, 'createHandleWithLocation',"Location: " + location)
    _debugMsg(debug, 'createHandleWithLocation',"username: " + username)
    _debugMsg(debug, 'createHandleWithLocation',"password: " + password)

    # Our 'prefix' is currently a number not a string - is this right?
    prefix = str(prefix)
    if baseurl.endswith('/'):
        uri = baseurl + prefix
    else:
        uri = baseurl + '/' + prefix
    if suffix != '': uri += "/" + suffix.lstrip(prefix+"/")
    _debugMsg(debug, 'createHandleWithLocation',"URI " + uri)
    #hdrs = {'If-None-Match': '*','Content-Type':'application/json'}
    hdrs = {'Content-Type':'application/json', 'Accept': 'application/json'}

    if checksum:
        new_handle_json = jsondumps([{'type':'URL','parsed_data':location}, {'type':'CHECKSUM','parsed_data': checksum}])
    else:
        new_handle_json = jsondumps([{'type':'URL','parsed_data':location}])

    _debugMsg(debug, 'createHandleWithLocation',"json: " + new_handle_json)         


    #response, content = http.request(uri, method='GET',headers=hdrs)
    #print str(response)
    #return None
    
    #try:
    response, content = http.request(uri,method='PUT',headers=hdrs,body=new_handle_json)
    #except:
    #    _debugMsg(debug, 'createHandleWithLocation', "An Exception occurred during Creation of " + uri)
    #    return None
    #else:
    #    _debugMsg(debug, 'createHandleWithLocation', "Request completed")
    
    if response.status != 201:
        _debugMsg(debug, 'createHandleWithLocation', "Not Created: Response status: "+str(response.status))
        print response
        if response.status == 400:
            _debugMsg('createHandleWithLocation', 'body json:' + new_handle_json)
    return None

        
	
    """
    make sure to only return the handle and strip off the baseuri if it is included
    """
    hdl = response['location']
    _debugMsg(debug,'hdl', hdl)
    if hdl.startswith(baseuri):
        hdl = hdl[len(baseuri):len(hdl)]
    elif hdl.startswith(baseuri + '/'):
        hdl = hdl[len(baseuri + '/'):len(hdl)]
  	
    _debugMsg(debug, 'final hdl', hdl)

    """
    update location. Use the previous created handle location
    """
    # TODO - add this later, but first get here successfully
    #updateHandleWithLocation(hdl,location)
    return hdl

createHandle('test_loc')


	
def updateHandleWithLocation(prefix,uri,value,suffix=''):
    """Update the 10320/LOC handle type field of the handle record.
         
    Parameters:
    prefix: URI to the resource, or the prefix if suffix is not ''.
    uri: baseurl + prefix.
    value: New value to store in "10320/LOC"
    suffix: The suffix of the handle. Default: ''.
    Returns True if updated, False otherwise.
         
    """
    debug = False
    
    loc10320 = getValueFromHandle(prefix,"10320/LOC",suffix)
    _debugMsg(debug, 'updateHandleWithLocation', "found 10320/LOC: " +str(loc10320))
    if loc10320 is None:
	loc10320 = '<locations><location id="0" href="'+value+'" /></locations>'
	response = modifyHandle(prefix,uri,"10320/LOC",loc10320,suffix)
	if not response:
	    _debugMsg(debug, 'updateHandleWithLocation', "Cannot update handle: " + uri \
					+ " with location: " + value)
            return False
    else:
	lt = LocationType(loc10320,debug)
	response = lt.checkInclusion(value)
	if response:
	    _debugMsg(debug, 'updateHandleWithLocation', "the location "+value+" is already included!")
	else:
	    resp, content = lt.addLocation(value)
	    if not resp: 
	        _debugMsg(debug, 'updateHandleWithLocation', "the location "+value \
						+" cannot be added")
	    else:
	        if not modifyHandle(prefix,"10320/LOC",content,suffix):
		    _debugMsg(debug,'updateHandleWithLocation', "Cannot update handle: " \
							+uri+ " with location: " + value)
		else:
		    _debugMsg(debug,'updateHandleWithLocation', "location added")
		    return True
	    return False 

	return True

	
def modifyHandle(prefix,uri,key,value,suffix=''):
    """Modify a parameter of a handle

    Parameters:
    prefix: URI to the resource, or the prefix if suffix is not ''.
    uri: baseuri + prefix
    key: The parameter "type" wanted to change
    value: New value to store in "data"
    suffix: The suffix of the handle. Default: ''.
    Returns True if modified or parameter not found, False otherwise.

    """

    if suffix != '': uri += "/" + suffix.lstrip(prefix+"/")

    debug = False
    
    _debugMsg(debug, 'modifyHandle',"URI " + uri)
    hdrs = {'Content-Type' : 'application/json'}

    if not key: return False

    handle_json = retrieveHandle(prefix,suffix)
    if not handle_json: 
        _debugMsg(debug, 'modifyHandle', "Cannot modify an unexisting handle: " + uri)
        return False
    
    handle = jsonloads(handle_json)
    KeyFound = False
    for item in handle:
        if 'type' in item and item['type']==key:
            KeyFound = True
            _debugMsg(debug, 'modifyHandle', "Found key " + key + " value=" + str(item['parsed_data']) )
        if value is None:
            del(item)
        else:
            item['parsed_data']=value
            del item['data']
        break;

    if KeyFound is False:
        if value is None:
            _debugMsg(debug, 'modifyHandle', "No value for Key " + key + " . Quiting")
            return True
    
        _debugMsg(debug, 'modifyHandle', "Key " + key + " not found. Generating new hash")
        handleItem={'type': key, 'parsed_data' : value}
        handle.append(handleItem)

    handle_json = jsondumps(handle)
    _debugMsg(debug, 'modifyHandle', "JSON: " + str(handle_json))    

    try:
        response, content = http.request(uri,method='PUT',headers=hdrs,body=handle_json)
    except:
        _debugMsg(debug, 'modifyHandle', "An Exception occurred during Creation of " + uri)
        return False
    else:
        _debugMsg(debug, 'modifyHandle', "Request completed")
    
    if response.status < 200 or response.status >= 300:
        _debugMsg(debug, 'modifyHandle', "Not Modified: Response status: "+str(response.status))
        return False
    
    return True


###############################################################################
# EPIC Client Command Line Interface #
###############################################################################

def search(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();

    ec = EpicClient(credentials)
    result = ec.searchHandle(credentials.prefix, args.key, args.value)

    sys.stdout.write(str(result))

def read(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();

    ec = EpicClient(credentials)
    if args.key == None:
        result = ec.retrieveHandle(credentials.prefix, args.handle)
    else:
        result = ec.getValueFromHandle(args.handle,args.key)

    sys.stdout.write(str(result))

def create(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();
    
    uid = uuid.uuid1();
    pid = credentials.prefix + "/" + str(uid)

    ec = EpicClient(credentials)
    result = ec.createHandle(pid,args.location,args.checksum)
    
    if result == None:
        sys.stdout.write("error")
    else:
        sys.stdout.write(result)


