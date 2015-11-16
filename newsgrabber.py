import yaml
import gmailtool
import logging


logger = logging.getLogger(__name__)

class ConfigNotFound(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr('Configuration for service ' + "'" + self.value + "'" + ' not found!')

class Config():

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


def parse_messages(messages, tags):

    for id, message in messages.iteritems():
        if message.is_multipart():
            print 'message id %s is multipart' % id
            for payload in message.get_payload():
                if payload.get_content_type() == 'text/html': # and id == '15096053accd1dfa':
                    data = payload.get_payload(decode=True)
                    new_data = create_metadata(id, message, 'html', data, tags)
                    print 'payload type is text/html'
                    file_name = 'pelican/content/' + id + '.html'
                    with open(file_name, 'w') as f:
                        f.write(new_data)
        else:
            metadata = create_metadata(id, message, 'markdown')
            content = create_content(message, 'markdown')
            print 'message id %s is text' % id
            file_name = 'pelican/content/' + id + '.md'
            print 'writing file %s' % file_name
            with open(file_name, 'w') as f:
                #f.write('Title')
                f.write(metadata)
                for c in content:
                    f.write('\n<' + c + '>')

def create_metadata(id, message, format, data=None, tags=None):

    if format == 'markdown':
        metadata = 'Title: %s\nDate: %s\n' % (message['Subject'].strip(), message['Date'].strip())
        return metadata

    if format == 'html':
        index = data.find('<meta')
        print 'index: %s' % index
        slug = '<meta name="Slug" content="' + str(id) + '">'
        tag = '<meta name="tags" content="' + tags + '">'
        new_data = data[:index] + slug + tag + data[index:]
        return new_data

def create_content(message, format):

    if format == 'markdown':
        con = message.get_payload().strip().split()
        content = [c for c in con if 'http' in c]
        return content



def main():

    try:
        config = GmailConfig('conf/newsgrabber.conf').get_gmail_config()
        gmail = gmailtool.Gmail(config['secrets_file'], config['storage_file'], config['scopes'])

    except KeyError:

        logger.error('Missing configuration parameter', exc_info=True)
        exit(1)

    except ConfigNotFound:
        logger.error('Configuration not found', exc_info=True)
        exit(1)

    for k in config['search']:
        label = config['search'][k]
        messages = gmail.fetch_messages(label['query'])
        parse_messages(messages, label['tags'])




if __name__ == '__main__':
    main()