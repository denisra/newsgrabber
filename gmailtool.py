#!/usr/bin/python

import logging
from oauth2client import file, client, tools
from apiclient.discovery import build
from httplib2 import Http
import argparse
import base64
import email

logger = logging.getLogger(__name__)

class Gmail:

    def __init__(self, secrets, storage, scopes):

        self.CLIENTSECRETS_LOCATION = secrets
        self.STORAGE_FILE = storage
        self.SCOPES = scopes
        self.messages = {}

# CLIENTSECRETS_LOCATION = 'conf/secret.json'
# STORAGE_FILE = 'conf/storage.json'
# SCOPES = [
#         'https://www.googleapis.com/auth/gmail.modify',
#         ]
# messages = {}

    def create_service(self):

        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        flags = parser.parse_args()

        store = file.Storage(self.STORAGE_FILE)
        creds = store.get()

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENTSECRETS_LOCATION, self.SCOPES)
            creds = tools.run_flow(flow, store, flags)

        GMAIL = build('gmail', 'v1', http=creds.authorize(Http()))

        return GMAIL


    def fetch_messages(self, query, user='me'):

        GMAIL = self.create_service()

        try:
            logger.info('Fetching messages for user %s and query=%s', user, query)
            message_ids = GMAIL.users().messages().list(userId=user, q=query, fields='messages(id,snippet)').execute().get('messages', [])

            logger.info('Total messages retrieved: %s', len(message_ids))
            for message_id in message_ids:
                #print "msg_id: %s" % message_id['id']
                msg_content = GMAIL.users().messages().get(userId='me', id=message_id['id'], format='raw').execute() #, fields='id,labelIds,payload,sizeEstimate,snippet,threadId,internalDate').execute() #.get('message', {})
                msg_str = base64.urlsafe_b64decode(msg_content['raw'].encode('ASCII'))
                mime_msg = email.message_from_string(msg_str)
                logger.info('id: %s - Subject: %s', message_id['id'], str(mime_msg['Subject']))
                self.messages[message_id['id']] = mime_msg
            # for msg_id, msg in messages.iteritems():
            #     #print msg_id, msg
            #     print '''
            #     id: %s
            #     To: %s
            #     Date Received: %s
            #     Subject: %s
            #         ''' % (msg_id, msg['Delivered-To'], msg['Date'], msg['Subject'])
            #     break

        except Exception, e:
            logger.error('Unable to fetch messages', exc_info=True)

        return self.messages

# def main():
#
#     messages = fetch_messages('to:denis.afonso+python@gmail.com')
#
#
# if __name__ == '__main__':
#     main()