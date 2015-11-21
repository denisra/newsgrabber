from urlparse import urljoin
from bs4 import BeautifulSoup as bs
import requests
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler('newsgrabber.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Url2Html:

    def __init__(self, url):

        self.url = url
        self.base_url = None
        self.content = None
        self.html = None
        logger.info('Url2Html initialized with url: %s', self.url)

    def parse_base_url(self):

        self.base_url = urljoin(self.url, '/')
        logger.info('Base_url = %s', self.base_url)
        return self.base_url

    def get_content(self):

        req = requests.get(self.url)
        if req.ok:
            self.content = req.content
            logger.info('Downloaded html content from %s', self.url)
            return self.content
        else:
            try:
                req.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error('Unable to get content from %s ', self.url, exc_info = True)




html = Url2Html('https://migrateup.com/store/advanced-python-book/')
#html = Url2Html('http://denisra.com/dasdas')
print html.parse_base_url()
html.get_content()