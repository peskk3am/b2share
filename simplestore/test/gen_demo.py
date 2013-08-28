import sys
import json
import requests
import argparse

from invenio.testutils import (make_test_suite, run_test_suite, InvenioTestCase,
                               test_web_page_content,
                               get_authenticated_mechanize_browser)
from invenio.config import CFG_SITE_SECURE_URL
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from pyvirtualdisplay import Display

# Make sure the server is running first:
# sudo java -jar selenium-server-standalone-2.35.0.jar -trustAllSSLCertificates


class DepositException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

    
def read_json(json_file):
    with open(json_file) as js:
        data = json.load(js)
    return data

            
def deposit_item(record, rec_num, verbose=False):
        if verbose:
            print "Record " + str(rec_num) + ": ...", 
         
        driver = webdriver.Remote('http://localhost:4444/wd/hub', 
            webdriver.DesiredCapabilities.HTMLUNITWITHJS)   
        driver.get('https://localhost/youraccount/login')

#*************************************
#browser.select_form(nr=0)
#    browser['nickname'] = username
#    browser['password'] = password
#    browser.submit()
#    username_account_page_body = browser.response().read()
#    
#    try:
#        #username_account_page_body.index("You are logged in as %s." % username)
#        username_account_page_body.index(username)
#    except ValueError:
#        raise InvenioTestUtilsBrowserException('ERROR: Cannot login as %s.' % username)
#    return browser
#***************************************        
        #CFG_SITE_SECURE_URL + '/youraccount/login', webdriver.DesiredCapabilities.HTMLUNITWITHJS)
        user_form = driver.find_element_by_name("nickname")
        user_form.send_keys("admin")
        user_form.submit()
        #for cookie in driver.get_cookies():
        #    print "%s -> %s" % cookie['name'], cookie['value']
        

        driver.get(CFG_SITE_SECURE_URL + '/deposit')       
        dep_soup = BeautifulSoup(driver.page_source)       
        
        sub_id = dep_soup.find_all(id='sub_id')[0]['value']   
        print "subid: %s" % sub_id     

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
                          
        domain = driver.find_element_by_id("uploadfiles").click()
        domain = driver.find_element_by_id("Generic").click()
        driver.implicitly_wait(5)
        print driver.page_source
        #driver.submit()                                
        #Do the submission
        #br.select_form(nr=0)
        #br['domain'] = ['Generic']
        #resp = br.submit()

        #add some metadata
        #br.select_form(nr=0)
        metadata_dict = record["metadata"]
        key_list = metadata_dict.keys()
        title = "Untitled"
        for key in key_list:
            print key
            #br[key] = metadata_dict[key]
            try:
                x = driver.find_element_by_id(key)
                print x.location_once_scrolled_into_view
                print "Found %s" % key
                x.send_keys(metadata_dict[key])
            except NoSuchElementException:
                print "Not found"
            except ElementNotVisibleException:
                print "Not visible"    
            if (key == 'title'):
                title = metadata_dict[key]
                
        driver.find_element_by_id("deposit").click()      
        #resp = br.submit()
        #driver.submit()
        #resp_text = resp.read()

        #check we got to the last page
        #if "Your submission will shortly be available" in resp_text:
        #    if verbose:
        #        print "Successful"
        #else:    
        #    raise DepositException("Unable to deposit record: " + title +
        #        '\n' + str(record))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="show verbose output",
                            action="store_true")
    parser.add_argument("-j", "--json", default="test_data.json",
                            help="input json file")    
    args = parser.parse_args()    
        
    test_data = read_json(args.json)

    records_list = test_data["records"]
    if args.verbose:
        print "Depositing %s records" % len(records_list)
    rec_num = 0    
    for r in records_list:
        rec_num = rec_num + 1
        try:
            deposit_item(r["record_content"], rec_num, args.verbose)
        except DepositException as e:
            print e.value

        
if __name__ == '__main__':
    main()
