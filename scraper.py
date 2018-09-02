# # -*- coding: utf-8 -*-
#!/usr/bin/python

import sys
import requests
from configobj import ConfigObj
import urlparse

import lxml.html

from utils import printIt

reload(sys)
sys.setdefaultencoding('utf8')

config = ConfigObj('config.ini')



class Target:
    def __init__(self, taragetName):
        """
        taragetName (String): Name of the target to initialize configration of.
        """
        assert (taragetName in config.keys()), "ERROR - Invalid Target Name %s" %(taragetName)
        targetConfig = config[taragetName]
        self.entryPageURL = targetConfig['PAGES']['ENTRY_URL']
        self.entryPageName = targetConfig['PAGES']['ENTRY_NAME']
        self.session = requests.Session()
        self.session.auth = (targetConfig['PAGES']['AUTH_USERNAME'], targetConfig['PAGES']['AUTH_PASSWORD'])
        self.signaturesURL = targetConfig['PAGE_SIGNATURES']['URL']
        self.crawlDepthLimit = targetConfig['LIMITS']['CRAWL_DEPTH_LIMIT']
        self.baseURL = targetConfig['PAGES']['BASE_URL']

    def loadPageSignatures(self):
        r = requests.get(self.signaturesURL)
        assert (200 <= r.status_code < 300), "ERROR - Unable to GET signatures page (%s): status code: %s" %(self.signaturesURL, r.status_code)
        rawPageSignatures = r.json()
        signatures = dict()
        for page in rawPageSignatures:
            signatures[page] = rawPageSignatures[page]
        self.signatures = signatures

    def parsePage(self, url, pageName):
        """
        url (String): URL of the page to scrape
        pageName (String): Name of page as per the pre saved configration

        $returns Object(url, nextPageName): (url of the next page to crawl, name of next page as per config)
        """
        if url == None and pageName == None:
            url, pageName = self.entryPageURL, self.entryPageName
        assert (pageName in self.signatures.keys()), "ERROR - Invalid Page Name %s" %(pageName)
        pageSignature = self.signatures[pageName]
        xpathButton = pageSignature['xpath_button_to_click']
        xpathTestQuery = pageSignature['xpath_test_query']
        xpathTestResult = pageSignature['xpath_test_result']
        nextPageName = pageSignature['next_page_expected']
        r = self.session.get(url)
        assert (200 <= r.status_code < 300), "ERROR - Unable to GET page %s (%s): status code: %s" %(pageName, url, r.status_code)
        html = lxml.html.fromstring(r.content)
        nextURL = html.xpath(xpathButton)[0].get("href")
        if nextURL.startswith('/') and not nextURL.startswith('//'):
            nextURL = urlparse.urljoin(self.baseURL, nextURL)
        fetchedResult = html.xpath(xpathTestQuery)
        if fetchedResult != xpathTestResult:
            return {"url": None, "nextPageName": nextPageName}
        return {"url": nextURL, "nextPageName": nextPageName}



def main():
    target = Target('LEGALSTART')
    target.loadPageSignatures()
    crawlDepthLimit = target.crawlDepthLimit
    crawlDepthCount = 0
    pageURL, pageName = target.entryPageURL, target.entryPageName
    while crawlDepthCount <= crawlDepthLimit:
        parsedResult = target.parsePage(pageURL, pageName)
        nextPagepageURL, nextPageName = parsedResult['url'], parsedResult['nextPageName']
        if nextPagepageURL == None:
            printIt("ALERT - Can’t move to page %s: page %s link has been malevolently tampered with!!"%(nextPageName, pageName))
            break
        printIt("Move to page %s"%(pageName))
        pageName = nextPageName
        pageURL = nextPagepageURL
        crawlDepthCount += 1
    if crawlDepthCount > crawlDepthLimit:
        printIt("ALERT - Reached Crawl Depth Limit %s"%(crawlDepthLimit))



if __name__ == '__main__':
    main()
