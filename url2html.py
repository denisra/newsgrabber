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

class ContentNotFound(Exception):
    pass


class Url2Html:

    def __init__(self, url):

        self.url = url
        self.base_url = urljoin(self.url, '/') #None
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

    def convert_relative_links(self):

        if self.content:
            content = bs(self.content, 'html5lib')
            for attr in [('a', 'href'), ('link', 'href'), ('img', 'src')]:
                for link in content.find_all(attr[0], **{attr[1]: True}):
                    href = link.get(attr[1])
                    #print 'link = %s' % link
                    if not href.startswith('http') and not href.startswith('#'):
                        absolute = urljoin(self.base_url, href)
                        link[attr[1]] = absolute
                        logger.info('Converted path %s to %s', href, absolute)
            self.html = content.prettify(formatter="html")
            logger.info('Successfully converted url %s to html.', self.url)
#            with open('test.html', 'w') as f:
#                f.write(self.html)
            return self.html
        else:
            logger.error('Content does not exist. Please call the get_content method first.')
            raise ContentNotFound


#html = Url2Html('https://migrateup.com/store/advanced-python-book/')
html = Url2Html('http://charlesleifer.com/blog/how-to-make-a-flask-blog-in-one-hour-or-less/')
print html.parse_base_url()
html.get_content()
html.convert_relative_links()