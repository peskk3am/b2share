import sys 

from invenio.testutils import (make_test_suite, run_test_suite, InvenioTestCase,
                               test_web_page_content,
                               get_authenticated_mechanize_browser)
from invenio.config import CFG_SITE_SECURE_URL
from bs4 import BeautifulSoup
import requests




        
def main():
        """Test "happy path" - deposit a new file with metadata"""

        proxy = {'http' : 'wwwcache.rl.ac.uk:8080',
                 'https' : 'wwwcache.rl.ac.uk:8080'}

        br = get_authenticated_mechanize_browser(username="admin", password="")
        res = br.open(CFG_SITE_SECURE_URL + '/deposit')
        dep_soup = BeautifulSoup(res.get_data())

        sub_id = dep_soup.find_all(id='sub_id')[0]['value']        

        form = {'nickname': 'admin',
                'password': ''}
        login = requests.post('%s/youraccount/login' % CFG_SITE_SECURE_URL,
                              data=form,
                              verify=False)
                                                 
        form = {'name': "simplestore_test_text.txt"}
        with open('data/simplestore_test_text.txt') as f:
            files = {'file': f}
            r = requests.post("%s/deposit/upload/%s" % (CFG_SITE_SECURE_URL, sub_id),
                          files=files,
                          data=form,
                          verify=False,
                          cookies=login.cookies)
        
        form = {'name': "simplestore_test_image.jpeg"}
        with open('data/simplestore_test_image.jpeg') as f:
            print "Opened file"
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

        #print resp.read()

        #add some metadata
        br.select_form(nr=0)
        br['title'] = 'Test Title'
        br['description'] = 'Test Description'
        br['creator'] = 'Test Bot'
        
        resp = br.submit()
        resp_text = resp.read()
        #print resp_text
        #check we got to the last page
        #self.assertIn("Your submission will shortly be available", resp_text)


#TEST_SUITE = make_test_suite(DepositTest)

if __name__ == '__main__':
    main()
