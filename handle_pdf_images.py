#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# vim:tw=80:ts=2:sw=2:colorcolumn=81:nosmartindent

import sys, logging, tempfile, shutil, os

#TODO: Remove this hack!!!
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sh'))

convert_options=["-background","white","-flatten","+matte","-density","300x300"]
convert_options_despeckle=["-background","white","-flatten","+matte","-density","600x600","-median","6"]

def process_pdf(content, noOCR, language, despeckle):
  from sh import pdftotext
  
  logging.debug("Extracting pdf contents using pdftotext")
  pdfText = unicode(pdftotext('-', '-', _in=content, _in_bufsize=10000))
  logging.debug("Extracted %d chars from the text", len(pdfText))

  if noOCR:
    logging.debug("OCR disabled, returning only pdf text")
  else:
    from sh import identify, tesseract, convert

    logging.debug("Starting OCR Operation")
    logging.debug("Extracing page numbers")

    pageNos = map(int,
        str(identify("-format", "%p ", "pdf:-", _in=content,_in_bufsize=10000)).\
            strip().split(' '))
    logging.debug("Found pages: %s", pageNos)
    
    allPages=u""
    for pageNo in pageNos:
      logging.debug("Processing page %d", pageNo)

      tmpFolder = tempfile.mkdtemp(prefix='imap-dms-ocr-tmp')

      co = convert_options if not despeckle else convert_options_despeckle
      logging.debug("Converting page to image in tmpfolder %s with options %s", tmpFolder, co)
      convert(co, "pdf:-[%d]" % (pageNo), tmpFolder+"/out.png",
           _in=content, _in_bufsize=10000)

      logging.debug("Running tesseract with language %s on file %s",
          language, tmpFolder+"/out.png")
      tesseract(tmpFolder+"/out.png", tmpFolder+"/out", "-l",language)
      
      f = open(tmpFolder+"/out.txt", "r")
      pageContent = unicode(f.read(), "utf-8")
      f.close()

      logging.debug("Found %d chars for this page", len(pageContent))
      allPages+=pageContent+u"\n"

      shutil.rmtree(tmpFolder)

    pdfText=pdfText.strip()+"\n\n\n"+allPages.strip()

  if(len(pdfText.strip())==0):
    logging.error("No text could be recognized")
    return None
  else:
    return pdfText

def process_image(content, noOCR, language, despeckle):
  if noOCR:
    logging.error("OCR disabled, no text available")
    return None
  from sh import tesseract, convert

  tmpFolder = tempfile.mkdtemp(prefix='imap-dms-ocr-tmp')

  logging.debug("Converting image in tmpfolder %s", tmpFolder)
  convert(convert_options, "-", tmpFolder+"/out.png", _in=content,
      _in_bufsize=10000)

  logging.debug("Running tesseract with language %s on file %s", 
      language, tmpFolder+"/out.png")
  tesseract(tmpFolder+"/out.png", tmpFolder+"/out", "-l",language)
  
  f = open(tmpFolder+"/out.txt", "r")
  content = unicode(f.read(), "utf-8")
  f.close()

  logging.debug("Found %d chars for this page", len(content))
   
  content=content.strip()

  if(len(content)==0):
    return None
  else:
    return content


  
def main(argv=None):
  if argv is None:
    argv = sys.argv

  if len(argv)!=5:
    print("Usage: %s [pdf|image] [filename] [0|1 for noOCR] [lang]" % (argv[0]))
    return 2
  
  logging.basicConfig(level=logging.DEBUG)

  f = open(argv[2], "rb")
  if(argv[1]=='pdf'):
    print(process_pdf(f.read(), int(argv[3])==1, argv[4]))
  elif(argv[1]=='image'):
    print(process_image(f.read(), int(argv[3])==1, argv[4]))
  else:
    print('Unkown type %s', argv[1])
    return 1

  f.close()

  return 0

if __name__ == "__main__":
  sys.exit(main())

