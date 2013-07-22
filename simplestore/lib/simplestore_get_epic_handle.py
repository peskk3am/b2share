#!/usr/bin/env python

import httplib2
from simplejson import loads as jsonloads 
from simplejson import dumps as jsondumps
from xml.dom import minidom

import uuid
import argparse
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

################################################################################
# Epic Client Class #
################################################################################

class EpicClient():
    """Class implementing an EPIC client."""
    
    def __init__(self, cred):
	"""Initialize object with connection parameters."""
	
        self.cred  = cred
        self.debug = cred.debug
	self.http = httplib2.Http(disable_ssl_certificate_validation=True)
	self.http.add_credentials(cred.username, cred.password)
	
	
    def _debugMsg(self,method,msg):
        """Internal: Print a debug message if debug is enabled."""
        if self.debug: 
            print "[",method,"]",msg
    
    # Public methods
	
    def createHandle(self,prefix,location,checksum=None,suffix=''):
	"""Create a new handle for a file.
	
	Parameters:
	prefix: URI to the resource, or the prefix if suffix is not ''.
	location: The location (URL) of the file.
	checksum: Optional parameter, store the checksum of the file as well.
	suffix: The suffix of the handle. Default: ''.
	Returns the URI of the new handle, None if an error occurred.
	
	"""
	
        if self.cred.baseuri.endswith('/'):
            uri = self.cred.baseuri + prefix
        else:
            uri = self.cred.baseuri + '/' + prefix

	if suffix != '': uri += "/" + suffix.lstrip(prefix+"/")
	self._debugMsg('createHandleWithLocation',"URI " + uri)
	hdrs = {'If-None-Match': '*','Content-Type':'application/json'}

	if checksum:
	    new_handle_json = jsondumps([{'type':'URL','parsed_data':location}, {'type':'CHECKSUM','parsed_data': checksum}])
	else:
	    new_handle_json = jsondumps([{'type':'URL','parsed_data':location}])

	    
	try:
	    response, content = self.http.request(uri,method='PUT',headers=hdrs,body=new_handle_json)
	except:
	    self._debugMsg('createHandleWithLocation', "An Exception occurred during Creation of " + uri)
	    return None
	else:
	    self._debugMsg('createHandleWithLocation', "Request completed")
	    
	if response.status != 201:
	    self._debugMsg('createHandleWithLocation', "Not Created: Response status: "+str(response.status))
            if response.status == 400:
                self._debugMsg('createHandleWithLocation', 'body josn:' + new_handle_json)
	    return None

        
	
        """
        make sure to only return the handle and strip off the baseuri if it is included
        """
        hdl = response['location']

	self._debugMsg('hdl', hdl)
        if hdl.startswith(self.cred.baseuri):
            hdl = hdl[len(self.cred.baseuri):len(hdl)]
        elif hdl.startswith(self.cred.baseuri + '/'):
            hdl = hdl[len(self.cred.baseuri + '/'):len(hdl)]
   	
    	self._debugMsg('final hdl', hdl)

	"""
        update location. Use the previous created handle location
        """
	self.updateHandleWithLocation(hdl,location)

	return hdl


###############################################################################
# EPIC Client Credentials Class #
###############################################################################
"""
get credentials from different storages, right now 
irods or filesystem. please store credentials in the 
following format, otherwise there are problems...
{
    "baseuri": "https://epic_api_endpoint here", 
    "username": "USER",
    "prefix": "YYY",
    "password": "ZZZZZZZ",
    "accept_format": "application/json",
    "debug": "False"
}
"""
class Credentials():
    
    """
    set variables to defaults.
    last 5 variables overwritten during parse()
    """
    def __init__(self, store, filename):
        self.store = store
        self.filename = filename
        self.debug = False
        self.baseuri = 'https://epic.sara.nl/v2_test/handles/'
        self.username = 'USER'
        self.prefix = 'YYY'
        self.password = 'ZZZZZ'
        self.accept_format = 'application/json'

    """
    parse credentials from json file on filespace/irods.
    if you want to use irods you need embededpython!
    """
    def parse(self):        
        if ((self.store!="os" and self.store!="irods") 
                                                or self.filename =="NULL"):
            if self.debug: 
                print "wrong cred store/path, using:%s %s %s" \
                % (self.baseuri,self.username,self.accept_format)
            return

        if self.store == "os":
            try:
                filehandle = open(self.filename,"r")
                tmp = jsonloads(filehandle.read())
                filehandle.close() 
            except Exception, err:
                print "problem while getting credentials from filespace"
                print "Error:", err
        else:
            print "this should not happen..."

        try:
            self.baseuri = tmp['baseuri']
            self.username = tmp['username']
            try:
                self.prefix = tmp['prefix']
            except Exception, err:
                self.prefix = self.username
            self.password = tmp['password']
            self.accept_format = tmp['accept_format']
            if tmp['debug'] == 'True':
                self.debug=True
        except Exception, err:
            print "missing key-value-pair in credentials file"
            
        if self.debug: 
            print "credentials from %s:%s %s %s %s" \
                % (self.store, self.baseuri, self.username, \
                   self.prefix, self.accept_format)
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

def modify(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();

    ec = EpicClient(credentials)
    result = ec.modifyHandle(args.handle,args.key,args.value)

    sys.stdout.write(str(result))

def delete(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();

    ec = EpicClient(credentials)
    result = ec.deleteHandle(args.handle)

    sys.stdout.write(str(result))

def relation(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();

    ec = EpicClient(credentials)
    result = ec.updateHandleWithLocation(args.ppid,args.cpid)
    sys.stdout.write(str(result))

def test(args):
    credentials = Credentials(args.credstore,args.credpath)
    credentials.parse();
    
    ec = EpicClient(credentials)
    
    print ""
    print "Retrieving Value of FOO from " + credentials.prefix + "/NONEXISTING (should be None)"
    print ec.getValueFromHandle(credentials.prefix,"FOO","NONEXISTING")
    
    print ""
    print "Creating handle " + credentials.prefix + "/TEST_CR1 (should be True)"
    print ec.createHandle(credentials.prefix + "/TEST_CR1","http://www.test.com/1") #,"335f4dea94ef48c644a3f708283f9c54"
    
    print ""
    print "Retrieving handle info from " + credentials.prefix + "/TEST_CR1"
    print ec.retrieveHandle(credentials.prefix +"/TEST_CR1")
    
    print ""
    print "Retrieving handle by url"
    result = ec.searchHandle(credentials.prefix, "URL", "http://www.test.com/1")
    print result

    print ""
    print "Modifying handle info from " + credentials.prefix + "/TEST_CR1 (should be True)"
    print ec.modifyHandle(credentials.prefix +"/TEST_CR1","uri","http://www.test.com/2")
    
    print ""
    print "Retrieving Value of EMAIL from " + credentials.prefix + "/TEST_CR1 (should be None)"
    print ec.getValueFromHandle("" + credentials.prefix +"/TEST_CR1","EMAIL")

    print ""
    print "Adding new info to " + credentials.prefix + "/TEST_CR1 (should be True)"
    print ec.modifyHandle(credentials.prefix + "/TEST_CR1","EMAIL","test@te.st")    

    print ""
    print "Retrieving Value of EMAIL from " + credentials.prefix + "/TEST_CR1 (should be test@te.st)"
    print ec.getValueFromHandle("" + credentials.prefix +"/TEST_CR1","EMAIL")

    print ""
    print "Updating handle info with a new 10320/loc type location 846/157c344a-0179-11e2-9511-00215ec779a8"
    print "(should be True)"
    print ec.updateHandleWithLocation(credentials.prefix + "/TEST_CR1","846/157c344a-0179-11e2-9511-00215ec779a8")

    print ""
    print "Updating handle info with a new 10320/loc type location 846/157c344a-0179-11e2-9511-00215ec779a9"
    print "(should be True)"
    print ec.updateHandleWithLocation(credentials.prefix + "/TEST_CR1","846/157c344a-0179-11e2-9511-00215ec779a9")
    
    print ""
    print "Retrieving handle info from " + credentials.prefix + "/TEST_CR1"
    print ec.retrieveHandle(credentials.prefix + "/TEST_CR1")
    
    print ""
    print "Deleting EMAIL parameter from " + credentials.prefix + "/TEST_CR1 (should be True)"
    print ec.modifyHandle(credentials.prefix + "/TEST_CR1","EMAIL",None)  

    print ""
    print "Retrieving Value of EMAIL from " + credentials.prefix + "/TEST_CR1 (should be None)"
    print ec.getValueFromHandle("" + credentials.prefix +"/TEST_CR1","EMAIL")

    print ""
    print "Updating handle info with a new 10320/loc type location 846/157c344a-0179-11e2-9511-00215ec779a8"
    print "(should be False)"
    print ec.updateHandleWithLocation(credentials.prefix + "/TEST_CR1","846/157c344a-0179-11e2-9511-00215ec779a8")

    print ""
    print "Removing 10320/loc type location 846/157c344a-0179-11e2-9511-00215ec779a8"
    print "(should be True)"
    print ec.removeLocationFromHandle(credentials.prefix + "/TEST_CR1","846/157c344a-0179-11e2-9511-00215ec779a8")

    print ""
    print "Removing 10320/loc type location 846/157c344a-0179-11e2-9511-00215ec779a8"
    print "(should be False)"
    print ec.removeLocationFromHandle(credentials.prefix + "/TEST_CR1","846/157c344a-0179-11e2-9511-00215ec779a8")
    
    print ""
    print "Retrieving handle info from " + credentials.prefix + "/TEST_CR1"
    print ec.retrieveHandle(credentials.prefix + "/TEST_CR1")
    
    print ""
    print "Deleting " + credentials.prefix + "/TEST_CR1 (should be True)"
    print ec.deleteHandle(credentials.prefix + "/TEST_CR1")  
    
    print ""
    print "Deleting (again) " + credentials.prefix + "/TEST_CR1 (should be False)"
    print ec.deleteHandle(credentials.prefix + "/TEST_CR1")  
    
    print ""
    print "Retrieving handle info from non existing " + credentials.prefix + "/TEST_CR1 (should be None)"
    print ec.retrieveHandle(credentials.prefix + "/TEST_CR1")   

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='EUDAT EPIC client API. Supports reading, querying, creating, modifying and deleting handle records.')
    parser.add_argument("credstore",choices=['os','irods'],default="NULL",help="the used credential storage (os=filespace,irods=iRODS storage)")
    parser.add_argument("credpath",default="NULL",help="path to the credentials")
    """parser.add_argument("-d", "--debug", help="Show debug output")"""
    
    subparsers = parser.add_subparsers(title='Actions',description='Handle record management actions',help='additional help')

    parser_create = subparsers.add_parser('create', help='creating handle records')
    parser_create.add_argument("location", help="location to store in the new handle record")
    parser_create.add_argument("--checksum", help="checksum to store in the new handle record")
    parser_create.set_defaults(func=create)

    parser_modify = subparsers.add_parser('modify', help='modifying handle records')
    parser_modify.add_argument("handle", help="the handle value")
    parser_modify.add_argument("key", help="the key of the field to change in the pid record")
    parser_modify.add_argument("value", help="the new value to store in the pid record identified with the supplied key")
    parser_modify.set_defaults(func=modify)

    parser_delete = subparsers.add_parser('delete', help='Deleting handle records')
    parser_delete.add_argument("handle", help="the handle value of the digital object instance to delete")
    parser_delete.set_defaults(func=delete)

    parser_read = subparsers.add_parser('read', help='Read handle record')
    parser_read.add_argument("handle", help="the handle value")
    parser_read.add_argument("--key", help="only read this key instead of the full handle record")
    parser_read.set_defaults(func=read)

    parser_search = subparsers.add_parser('search', help='Search for handle records')
    parser_search.add_argument("key", choices=['URL','CHECKSUM'],help="the key to search")
    parser_search.add_argument("value", help="the value to search")
    parser_search.set_defaults(func=search)

    parser_relation = subparsers.add_parser('relation', help='Add a (parent,child) relationship between the specified handle records')
    parser_relation.add_argument("ppid", help="parent handle value")
    parser_relation.add_argument("cpid", help="child handle value")
    parser_relation.set_defaults(func=relation)

    parser_test = subparsers.add_parser('test', help='Run test suite')
    parser_test.set_defaults(func=test)

    args = parser.parse_args()
    args.func(args)
