import sys
import json
import requests

from invenio.testutils import (make_test_suite, run_test_suite, InvenioTestCase,
                               test_web_page_content,
                               get_authenticated_mechanize_browser)
from invenio.config import CFG_SITE_SECURE_URL
from bs4 import BeautifulSoup


class DepositException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

    
def read_json(json_file):
    with open(json_file) as js:
        data = json.load(js)
    return data

            
def deposit_item(record, verbose, rec_num):
        if verbose:
            print "Record " + str(rec_num) + ": ...", 
        br = get_authenticated_mechanize_browser(username="admin", password="")
        res = br.open(CFG_SITE_SECURE_URL + '/deposit')
        dep_soup = BeautifulSoup(res.get_data())

        sub_id = dep_soup.find_all(id='sub_id')[0]['value']        

        form = {'nickname': 'admin',
                'password': ''}
        login = requests.post('%s/youraccount/login' % CFG_SITE_SECURE_URL,
                              data=form,
                              verify=False)
        
        files_list = record["files"]
        for fl in files_list:
            if fl.has_key('dir'):
                test_data_dir = fl["dir"]
            else:
                test_data_dir = 'data/'
            filename = fl["filename"]                             
            form = {'name': filename}
            with open('%s%s' % (test_data_dir, filename)) as f:
                files = {'file': f.read()}
                r = requests.post("%s/deposit/upload/%s" % (CFG_SITE_SECURE_URL, sub_id),
                          files=files,
                          data=form,
                          verify=False,
                          cookies=login.cookies)
                                            
        #Do the submission
        br.select_form(nr=0)
        br['domain'] = ['Generic']
        resp = br.submit()

        #add some metadata
        br.select_form(nr=0)
        metadata_dict = record["metadata"]
        key_list = metadata_dict.keys()
        title = "Untitled"
        for key in key_list:
            br[key] = metadata_dict[key]
            if (key == 'title'):
                title = metadata_dict[key]
              
        resp = br.submit()
        resp_text = resp.read()

        #check we got to the last page
        if "Your submission will shortly be available" in resp_text:
            if verbose:
                print "Successful"
        else:    
            raise DepositException("Unable to deposit record: " + title +
                '\n' + str(record))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) > 3:
        print "Usage: " + argv[0] + " [-v] [json file]"
        return
           
    # set defaults
    json_file = "test_data.json"
    verbose = False

    if len(argv) > 1:
        if argv[1] == '-v' or argv[1] == '--verbose':
            verbose = True
            del argv[1]
        
        if len(argv) > 1:    
            json_file = argv[1]
        
    test_data = read_json(json_file)

    records_list = test_data["records"]
    if verbose:
        print "Depositing " + str(len(records_list)) + " records"
    rec_num = 0    
    for r in records_list:
        rec_num = rec_num + 1
        try:
            deposit_item(r["record_content"], verbose, rec_num)
        except DepositException as e:
            print e.value

        
if __name__ == '__main__':
    main()
    