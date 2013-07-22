from invenio.config import CFG_SITE_SECURE_URL
from simplestore_epic import createHandle

def getHandle():
    recid = 7
    location = CFG_SITE_SECURE_URL + '/record/' + str(recid)
    #location = "http://www.bbc.co.uk"
    pid = createHandle(location)