#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# vim:tw=80:ts=2:sw=2:colorcolumn=81:nosmartindent

import logging, sys, os, os.path, imaplib, email, email.mime
import email.mime.nonmultipart, email.charset, platform

import tools

from handle_pdf_images import process_pdf, process_image
content_processors={
  "application/pdf": process_pdf,
  "image/png": process_image,
  "image/jpeg": process_image,
  "image/jpg": process_image
}

#Defaults config
defaultConfigFile=tools.getDefaultPath('imap_dms.defaults')
logging.basicConfig(level=logging.DEBUG)

def handle_part(conf, msg, part, tags):
  logging.debug('Found part filename=%s, type=%s', part.get_filename(),
      part.get_content_type())
 
  if(part.get_filename() in conf.get('Options', 'skip_filenames')):
    logging.debug("Skipping because filename is on skiplist")
    return

  if(part.get_content_type() in conf.get('Options', 'skip_contenttypes')):
    logging.debug("Skipping because MIME-type is on skiplist")
    return

  if part.get_content_type() in content_processors:
    f=content_processors[part.get_content_type()]
    logging.debug("Running processor %s", str(f))
    
    noOcr = 'noocr' in tags
    
    #Check language settings
    tagLang =  set(conf.get('Options', 'available_languages')) & set(tags)
    if(len(tagLang)==0):
      logging.debug('No language selected via tags, using default %s',
          conf.get('Options', 'default_language'))
      language=conf.get('Options', 'default_language')
    elif(len(tagLang)==1):
      language=tagLang.pop()
      logging.debug('Found language %s from tags', language)
    else:
      logging.error('Found more than one language in tags, using default')
      language=conf.get('Options', 'default_language')

    newname = '%s.%s' % (part.get_filename(), 'txt')
    newcontent = f(part.get_payload(decode=True), noOcr, language)

    if newcontent is not None:
      logging.debug("Recieved %d chars, saving to mail", len(newcontent))

      newpart=tools.MIMEUTF8QPText(newcontent)      
      newpart.add_header('Content-Disposition', 'attachment', filename=('utf-8',
        '', newname.encode('utf-8')))
      msg.attach(newpart)
    else:
      logging.error("Could not recognize any text for this attachment")
  else:
    logging.error('Don\'t know how to handle this mime-type')


def usage(name):
  print("IMAP-DMS Version %s" % (tools.__version__))
  print("")
  print("Usage: %s [configuration file]" % name)
  print("""
IMAP-DMS downloads new messages from an IMAP folder specified in the
configuration file. It then turns every attachment which is not plain text into
plain text by using multiple utitilies likes pdftotext or OCR.

The purpose of this script is to make documents on an IMAP server searchable
""")

def main(argv):
  if len(argv)!=2:
    usage(argv[0])
    return 1

  #Read Configuration
  logging.debug('Parsing configuration from file %s', argv[1])
  logging.debug('Defaults are stored in %s', defaultConfigFile)

  conf=tools.DMSConfigParser()
  if(len(conf.read([defaultConfigFile, argv[1]]))!=2):
    logging.error('Could not read config file')
    return 1

  logging.debug('Connecting to host %s', conf.get('Server','host'))
  if (conf.get('Server', 'usessl')):
    M = imaplib.IMAP4_SSL(conf.get('Server', 'host'))
  else:
    M = imaplib.IMAP4(conf.get('Server', 'host'))
  logging.debug('Connection established')

  logging.debug('Logging in with user %s', conf.get('Server', 'user'))
  M.login(conf.get('Server', 'user'),conf.get('Server', 'password'))

  logging.debug('Searching for messages in folder %s',
      conf.get('Folders','check_folder'))
  M.select(conf.get('Folders', 'check_folder'))
  recode, uids = M.uid('search', None, '(NOT HEADER %s "")' %
      conf.get('Options', 'header'))
  logging.debug('Found %d messages: %s', len(uids[0].split()), uids[0])

  for uid in map(int, uids[0].split()):
    logging.debug('Fetching message ID %d', uid)
    recode, data = M.uid('fetch', uid, '(RFC822)')
    msg = email.message_from_string(data[0][1])
    msgTimestamp = email.utils.parsedate(msg['Date'])

    logging.debug('Message is "%s" from "%s"', msg['Subject'], msg['From'])

    #Parse out tags (docs+tag1+tag2@domain.tld)
    _, toAddr = email.utils.parseaddr(msg['To'])
    tags = toAddr.partition('@')[0].split('+')[1:]
    logging.debug('Extracted tags %s', tags)

    for part in msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue

      handle_part(conf, msg, part, tags)

    #Modify the message somehow
    msg[conf.get('Options', 'header')] = '%s at host %s' % (email.utils.formatdate(),
    platform.node())

    #Save the new message
    logging.debug('Appending new message to %s with flags %s',
        conf.get('Folders', 'save_folder'), conf.get('Options', 'flags'))
    logging.debug('Original message has date %s', msgTimestamp)

    M.append(conf.get('Folders', 'save_folder'), "(%s)" % str.join(" ",
      conf.get('Options', 'flags')), imaplib.Time2Internaldate(msgTimestamp),
      msg.as_string())

    #Copy old message to backup folder
    if conf.get('Folders', 'original_folder') is not None:
      logging.debug('Copying old message to %s',
          conf.get('Folders', 'original_folder'))
      recode = M.uid('copy', uid, conf.get('Folders', 'original_folder'))
      if(recode[0] != 'OK'):
        logging.error('Could not move original mail %d to folder %s: %s', uid,
        conf.get('Folders', 'original_folder'), recode)
        raise imaplib.error('Could not copy message')
    
    #Delete old message
    logging.debug('Deleting old message from %s', conf.get('Folders', 'check_folder'))
    recode = M.uid('store', uid , '+FLAGS', '(\Deleted)')
    M.expunge()
    logging.debug('Deletion Result %s', recode)

  logging.debug('Closing folder and logging out')
  M.close()
  M.logout()

if __name__ == '__main__':
  sys.exit(main(sys.argv))
