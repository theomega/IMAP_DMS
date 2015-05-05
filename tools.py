# -*- coding: utf-8 -*-
# vim:tw=80:ts=2:sw=2:colorcolumn=81:nosmartindent

from ConfigParser import ConfigParser
import os
import email.header, email.mime.nonmultipart, logging

__version__ = '0.0.1'

class DMSConfigParser(ConfigParser):
  def get(self, section, option):
    """ Get a parameter if the returning value is a list, convert string value
    to a python list.  This code is taken from
    http://stackoverflow.com/a/335754/61855"""

    value = ConfigParser.get(self, section, option)
    if ((value!=None) and (value!='') and
       (value[0] == "[") and (value[-1] == "]")):
        return eval(value)
    else:
        return value

def getDefaultPath(n):
  """ Returns the absolute path of a file which resides in the script
  directory"""
  return os.path.join(os.path.split(os.path.realpath(__file__))[0],n)

def decodeHeader(s):
  """Decodes a encoded header. This code is taken partly from
  http://stackoverflow.com/a/7331577/61855"""
  dh = email.header.decode_header(s)
  return ' '.join([ unicode(t[0], t[1] or 'ASCII') for t in dh ])

class MIMEUTF8QPText(email.mime.nonmultipart.MIMENonMultipart):
  def __init__(self, payload):
    email.mime.nonmultipart.MIMENonMultipart.__init__(self, 'text', 'plain',
                                                      charset='utf-8')

    utf8qp=email.charset.Charset('utf-8')
    utf8qp.body_encoding=email.charset.QP

    self.set_payload(payload, charset=utf8qp)

def getCompleter(tags):
  logging.debug('Returning Completer for tags %s', tags)
  def complete(text, state):
    l=[x+" " for x in tags if x.lower().startswith(text.lower())]+[None]
    return l[state]

  return complete

import time as _time
from datetime import timedelta, tzinfo

ZERO = timedelta(0)
HOUR = timedelta(hours=1)

STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):
  def utcoffset(self, dt):
    if self._isdst(dt):
      return DSTOFFSET
    else:
      return STDOFFSET

  def dst(self, dt):
    if self._isdst(dt):
      return DSTDIFF
    else:
      return ZERO

  def tzname(self, dt):
    return _time.tzname[self._isdst(dt)]

  def _isdst(self, dt):
    tt = (dt.year, dt.month, dt.day,
       dt.hour, dt.minute, dt.second,
       dt.weekday(), 0, 0)
    stamp = _time.mktime(tt)
    tt = _time.localtime(stamp)
    return tt.tm_isdst > 0

Local = LocalTimezone()

def formatDate(d, localtime=False, usegmt=False):
  t = d.timetuple()
  ts = _time.mktime(t)
  return email.utils.formatdate(ts, localtime, usegmt)
