import yaml
import gmailtool
import logging
import os
import url2html
from urlparse import urlparse, parse_qs
from bs4 import BeautifulSoup as bs

logger = logging.getLogger(__name__)

class ConfigNotFound(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr('Configuration for service ' + "'" + self.value + "'" + ' not found!')

class Config:

    def __init__(self, config_file):

        self.config_file = config_file
        self.config = {}
        self.setup_logging()

    def load_config(self):

        logger.info('Loading configuration file')

        try:
            with open(self.config_file, 'r') as config_file:
                self.config = yaml.load(config_file)

        except IOError:

            logger.error('Unable to load the config file', exc_info=True)

        else:

            logger.info('Configuration file loaded')

    def get_config(self, service):

        try:
            conf = self.config[service]

        except KeyError:

            raise ConfigNotFound(service)

        else:
            return conf

    def setup_logging(self):

        logging.basicConfig(level=logging.INFO)
        handler = logging.FileHandler('newsgrabber.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)


class GmailConfig(Config):

    def __init__(self, config_file):

        Config.__init__(self, config_file)
        self.load_config()
        self.gmail = self.get_config('gmail')

    def get_gmail_config(self):

        return self.gmail


def get_video_id(url):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None

def parse_url(urls, pattern):

    logger.debug('Trying to match url pattern = %s', pattern)

    for url in urls:
        if urlparse(url).scheme in ['http', 'https'] and pattern in urlparse(url).hostname:
            logger.debug('Found a match: %s', url)
            return True
    return False

def get_links(data, extract_links):

    content = bs(data, 'html5lib')
    links = []
    for link in content.find_all('a', href = True):
        links.append(link.get('href'))

    res = list(links)

    if links and parse_url(links, extract_links['from']):
        for link in links:
            query = urlparse(link)
            if extract_links['from'] in query.hostname:
                logger.info('Removing %s from links', link)
                res.remove(link)
                continue
            for i in extract_links['ignore']:
                if i in query.hostname:
                    logger.info('Removing %s from links', link)
                    res.remove(link)
                    continue
    else:
        return None
    if len(res) != 1:
        print res
        exit(1)
    else:
        return res

def parse_messages(messages, category, content_dir, extract_links=None):

    for msg_id, message in messages.iteritems():
        if message.is_multipart():
            print 'message id %s is multipart' % msg_id
            for payload in message.get_payload():
                if payload.get_content_type() == 'text/html': # and id == '15096053accd1dfa':
                    data = payload.get_payload(decode=True)
                    if extract_links:
                        links = get_links(data, extract_links)
                        if links:
                            u2h = url2html.Url2Html(str(links[0]).strip())
                            try:
                                u2h.get_content()
                            #except requests.exceptions.HTTPError:
                            except :
                                logger.error('Unable to download content', exc_info=True)
                            if not u2h.content:
                                continue
                            data = u2h.convert_relative_links()
                    new_data = create_metadata(msg_id, message, 'html', data, category)
                    #print 'payload type is text/html'
                    file_name = content_dir + msg_id + '.html'
                    if not os.path.isfile(file_name):
                        with open(file_name, 'w') as f:
                            f.write(new_data)
                    else:
                        logger.warn('Skipping. File already exists: %s', file_name)
        else:
            #metadata = create_metadata(msg_id, message, 'markdown')
            content = create_content(message, 'markdown')
            if len(content) > 1:
                logger.warn('Total of %s links in msg id %s', len(content), msg_id)
                continue
            if 'youtu.be' in str(content[0]) or 'youtube.com' in str(content[0]):
                logger.info('Message %s contains an youtube link: %s', msg_id, content)
                video_id = get_video_id(str(content[0]))
                logger.info('Youtube video id: %s', video_id)
                metadata = create_metadata(msg_id, message, 'rst', None, category)
                data = metadata + '\n\n' + '.. youtube:: ' + video_id
                ext = '.rst'
            else:
                ext = '.html'
                u2h = url2html.Url2Html(content[0])
                try:
                    u2h.get_content()
                #except requests.exceptions.HTTPError:
                except :
                    logger.error('Unable to download content', exc_info=True)
                if not u2h.content:
                    continue
                html = u2h.convert_relative_links()
                print 'message id %s is text' % msg_id
                data = create_metadata(msg_id, message, 'html', html, category)
            #file_name = content_dir + msg_id + '.md'
            file_name = content_dir + msg_id + ext
            logger.info('Writing file %s', file_name)
            if not os.path.isfile(file_name):
                with open(file_name, 'w') as f:
                    #f.write('Title')
                    if ext == '.md':
                        #f.write(metadata)
                        for c in content:
                            f.write('\n<' + c + '>')
                    else:
                    #f.write(message.get_payload(decode=True).strip())
                        f.write(data)
                    #for c in content:
                    #    f.write('\n<' + c + '>')
            else:
                logger.warn('Skipping. File already exists: %s', file_name)

def create_metadata(msg_id, message, fmt, data=None, category=None):

    if fmt == 'markdown':
        metadata = 'Title: %s\nDate: %s\nSlug: %s\n' % (message['Subject'].strip(), message['Date'].strip(), str(msg_id))
        return metadata

    if fmt == 'html':
        content = bs(data, 'html5lib')
        summary = None
        for link in content.find_all('meta'):
            if link.get('name') == 'summary':
                summary = link #.get('content')
        if summary is None:
            for link in content.find_all('meta'):
                if link.get('name') == 'description' or link.get('property') == 'og:description':
                    summary = '<meta name="summary" content="' + link.get('content').encode('utf-8') + '"/>\n'
        if summary is None:
            summary = '<meta name="summary" content="' + message['Subject'] + '"/>\n'

        index = data.find('<meta')
        slug = '<meta name="Slug" content="' + str(msg_id) + '"/>\n'
        categories = '<meta name="category" content="' + category + '"/>\n'
        #print categories
        #   metadata = data[:index] + slug + categories + str(summary) + title + data[index:]
        #else:
        new_data = data[:index] + slug + categories + str(summary) + data[index:]
        metadata = bs(new_data, 'html5lib')
        if not metadata.title:
            title = metadata.new_tag('title')
            title.string = str(message['Subject']).strip()
            metadata.head.insert_after(title)
        return metadata.prettify(formatter="html").encode('utf-8')

    if fmt == 'rst':
        title_under = '#' * len(message['Subject'])
        title = message['Subject'] + '\n' + title_under + '\n\n'
        date = ':date: ' + message['Date'].strip() + '\n'
        slug = ':slug: ' + str(msg_id) + '\n'
        category = ':category: ' + category + '\n'
        metadata = title + date + slug + category
        return metadata

def create_content(message, fmt):

    if fmt == 'markdown':
        con = message.get_payload().strip().split()
        content = [c for c in con if 'http' in c]
        return content



def main():

    try:
        config = GmailConfig('conf/newsgrabber.conf').get_gmail_config()
        gmail = gmailtool.Gmail(config['secrets_file'], config['storage_file'], config['scopes'])
        conf_dir = Config('conf/newsgrabber.conf')
        conf_dir.load_config()
        content_dir = conf_dir.get_config('pelican')['content_dir']
        logger.info('Content directory: %s', content_dir)

    except KeyError:

        logger.error('Missing configuration parameter', exc_info=True)
        exit(1)

    except ConfigNotFound:
        logger.error('Configuration not found', exc_info=True)
        exit(1)

    for k in config['search']:
        label = config['search'][k]
        messages = gmail.fetch_messages(label['query'])
        parse_messages(messages, label['category'], content_dir, config['extract_links'])




if __name__ == '__main__':
    main()