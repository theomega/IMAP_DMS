# -*- coding: utf-8 -*- 
# vim:tw=80:ts=2:sw=2:colorcolumn=81:nosmartindent

from ConfigParser import SafeConfigParser
import os

class DMSConfigParser(SafeConfigParser):
  def get(self, section, option):
    """ Get a parameter
    if the returning value is a list, convert string value to a python list"""
    value = SafeConfigParser.get(self, section, option)
    if (value[0] == "[") and (value[-1] == "]"):
        return eval(value)
    else:
        return value

def getDefaultPath(n):
  return os.path.join(os.path.split(os.path.realpath(__file__))[0],n)

