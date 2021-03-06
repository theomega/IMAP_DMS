#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:tw=80:ts=2:sw=2:colorcolumn=81:nosmartindent

import logging, sys, os, os.path, imaplib, email, email.mime, email.header
import email.mime.nonmultipart, email.mime.multipart, email.charset
import email.parser, platform, re, email.mime.text, email.encoders, mimetypes
import argparse, readline, getpass, locale
from datetime import date, datetime, time
import itertools

import tools

#Defaults config
defaultConfigFile=tools.getDefaultPath('imap_dms.defaults')

def downloadTags(M, conf):
  logging.debug('Parsing messages in folder %s',
      conf.get('Folders','save_folder'))
  M.select(conf.get('Folders', 'save_folder'))

  recode, subjects = M.uid('fetch', '1:*', '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
  subjects = map(lambda x: tools.decodeHeader(x[1].replace("Subject:",
    "").strip()), subjects[0::2])
  logging.debug("Found %s", subjects)
  tags = map(lambda x: re.findall('\[([a-zA-Z0-9 ]+)\]', x), subjects)
  tags = set(itertools.chain.from_iterable(tags))

  logging.debug('Found Tags: %s', tags)

  return tags

def updateTags(M, conf):
  logging.debug('Upading tags')
  tags = downloadTags(M, conf)

  tagsFile = os.path.expanduser(conf.get('Client', 'tags_file'))
  logging.debug('Saving tags to %s', tagsFile)
  f = open(tagsFile, 'w')
  for t in sorted(tags):
    f.write("%s\n" % (t))
  f.close()
  logging.debug('Finished saving tags')

def addDocument(M, conf, documents):
  filepaths = map(os.path.realpath, documents)
  filenames = [os.path.split(fp)[1] for fp in filepaths]

  logging.info('Adding the following documents:')

  #Check if all files exist:
  for f in filepaths:
    logging.info('  %s', f)
    if(not os.path.exists(f)):
      logging.error("File %s does not exist, abort", f)
      return 1

  tagsFile = os.path.expanduser(conf.get('Client', 'tags_file'))
  if os.path.isfile(tagsFile):
    f = open(tagsFile, 'r')
    tags = [x.strip() for x in f.readlines()]
    f.close()
  else:
    tags = []

  #Read Title
  historyPathTitle = os.path.expanduser(conf.get('Client','history_file_title'))
  if os.path.exists(historyPathTitle):
     readline.read_history_file(historyPathTitle)

  readline.parse_and_bind("tab: None")
  title = unicode(raw_input('Enter Title: '), sys.stdin.encoding)
  title = title.strip()
  logging.debug("Got title '%s' from user", title)

  if(len(title)==0):
    logging.debug('No title specified, taking first filename %s', filenames[0])
    title = filenames[0]

  readline.write_history_file(historyPathTitle)
  readline.clear_history()

  #Read Tags
  readline.parse_and_bind("tab: complete")
  readline.set_completer(tools.getCompleter(tags))

  historyPathTags = os.path.expanduser(conf.get('Client','history_file_tags'))
  if os.path.exists(historyPathTags):
     readline.read_history_file(historyPathTags)

  tags = unicode(raw_input('Enter Tags: '), sys.stdin.encoding)
  tags = tags.strip()
  logging.debug("Got tags '%s' from user", tags)

  readline.write_history_file(historyPathTags)
  readline.clear_history()

  #Read Datetime
  readline.parse_and_bind("tab: None")
  formatString = conf.get('Client','date_format')

  today = date.today().strftime('%d.%m.%Y')
  while True:
    s = raw_input('Enter Date (format: %s, return for today): ' % (today))
    s = s.strip()
    if(len(s)==0):
      timestamp = datetime.combine(date.today(), time(0,0,0,0))
      break

    try:
      timestamp = datetime.strptime(s, formatString)
      break
    except ValueError:
      logging.error("Invalid date '%s' for formatstring %s", s, formatString)
      continue

  #timestamp = timestamp.replace(tzinfo=tools.Local)
  logging.debug("Found date %s", timestamp)

  #Construct subject of the mail
  if(len(tags)>0):
    subject=title+" "+''.join(['['+t.strip()+']' for t in tags.split(' ')])
  else:
    subject=title
  logging.debug("Subject of mail will be '%s'", subject)

  #Construct Sender
  if(len(conf.get('Client','sender'))>0):
    sender = conf.get('Client','sender')
  else:
    sender = "%s@%s" % (getpass.getuser(), platform.node())
  logging.debug("Sender of mail will be '%s'", sender)

  #Construct Reciever
  if(len(conf.get('Client','receiver'))>0):
    receiver = conf.get('Client', 'receiver')
  else:
    receiver = "%s@%s" % (conf.get('Server', 'user'), conf.get('Server','host'))
  logging.debug("Receiver of the mail will be '%s'", receiver)
  msg = email.mime.multipart.MIMEMultipart()
  msg['Subject'] = unicode(subject)
  msg['From'] = unicode(sender)
  msg['To'] = unicode(receiver)
  msg['Date'] = tools.formatDate(timestamp, True)
  msg['Message-ID'] = email.utils.make_msgid()
  msg['User-Agent'] = 'IMAP-DMS version %s' % (tools.__version__)

  #Add Text part (quite useless, for some mailclients necessary)
  text=u"""
This Mail contains the following files:
%s
It was created on '%s' on host '%s' by user '%s'.
""" % (
  ''.join(['- '+l+'\n' for l in filenames]),
  str(datetime.now()),
  platform.node(),
  getpass.getuser()
  )

  textPart = tools.MIMEUTF8QPText(text)
  msg.attach(textPart)

  for processFile in zip(filenames, filepaths):
    #Construct mime-type
    mimetype=mimetypes.guess_type(processFile[1])
    if(mimetype is None or mimetype[0] is None):
      logging.error("Could not get mime-type for '%s', abort", processFile[1])
      return 1

    logging.debug('Mime Type of file %s is %s', processFile[1], mimetype)
    mimetype=mimetype[0].split('/')

    #Add mime-part to message
    binpart = email.mime.nonmultipart.MIMENonMultipart(mimetype[0], mimetype[1])
    f = open(processFile[1], 'r')
    binpart.set_payload(f.read())
    email.encoders.encode_base64(binpart)
    f.close()
    binpart.add_header('Content-Disposition', 'attachment', filename=('utf-8',
      '', processFile[0].encode('utf-8')))
    msg.attach(binpart)

  imaptimestamp=imaplib.Time2Internaldate(
      timestamp.replace(tzinfo=tools.Local).timetuple())
  logging.info('Uploading message')
  logging.debug('Saving message to IMAP Folder %s with timestmap %s',
      conf.get('Folders','check_folder'), imaptimestamp)

  M.append(conf.get('Folders', 'check_folder'), "()", imaptimestamp,
      msg.as_string())
  logging.info('Finished uploading')

def main(argv):
  cmd = argparse.ArgumentParser(description='Add a new document')
  cmd.add_argument('-l', '--localtags', action='store_true', default=False,
                               help='use local stored tags, do not download')

  cmd.add_argument('-c', '--config', required=True, help='configuration file')
  cmd.add_argument('-v', '--verbose', action='store_true', default=False,
                   help='verbose debugging output')
  cmd.add_argument('filename', nargs='+', help='file to add')
  args = cmd.parse_args(argv[1:])

  if(args.verbose):
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)

  logging.debug('Parsed cmd-line is %s', args)

  #Read Configuration
  logging.debug('Parsing configuration from file %s', args.config)
  logging.debug('Defaults are stored in %s', defaultConfigFile)

  conf=tools.DMSConfigParser()
  if(len(conf.read([defaultConfigFile, args.config]))!=2):
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

  if(not args.localtags):
    updateTags(M, conf)

  result = addDocument(M, conf, [unicode(f, locale.getpreferredencoding()) for f in
    args.filename])

  logging.debug('Closing folder and logging out')
  M.logout()

  return result

if __name__ == '__main__':
  sys.exit(main(sys.argv))
