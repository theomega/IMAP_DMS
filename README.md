The Problem / The Motivation
===========================

When searching for Document Management Systems (DMS) you can find a large amount
of commercial and open source projects. Each of them has its unique feature set,
but all of them missed some features I required and most of them where much to
heavy.

What I needed was:

   - Adding new documents must be as simple as possible.
   - PDFs are the main format as every scanner produces them and everybody can
     open them
   - The full text of all documents must be searchable.
   - The full text must be extracted from scanned documents using OCR.
   - The full text which is contained in PDFs must be available for searching.
   - A Backup must be easily possible.
   - No folder structures where you have to decide whether a document is more
     'tax' or more 'invoices'. A system consisting of tags is much better suited
     here.

This project presents a unique approach which fulfils all the requirements
specified above. 

The Idea
========

The main idea of this project is to use an existing IMAP server to store the
documents: An IMAP Server already provides the storage of ''objects'' (in this
case documents) and a sophisticated searching. Many tool exists that can be used
to backup an IMAP account. By using this approach, existing IMAP accounts and
servers can be reused to store the documents. The access to the documents can be
done using ordinary IMAP clients like Mozilla Thunderbird or web clients like
Roundcube. They all support searching for documents and downloading/viewing
them.

Files can be added to the IMAP Document Storage easily by using emails. The
documents are their attachments, so an single email can contain multiple
documents. As the subject can be searched easily, this can be seen as the
identifier for the document(s). Tags can either be done using IMAP keywords (the
flags of Thunderbird) or by simply adding tags like `[invoice]` to the subject.
As you can search only in the subject in most email programs, you can search
for tags very easily.

The only missing part is the creation of the full text which can be searched by
the IMAP server. As IMAP servers can search in plain text attachments, all other
(binary) attachments have to be turned into plain text for searching.

The Project
==========

This script reads an IMAP mailbox (aka an IMAP folder) and search for all mails
which it has not processed already. For each of the mails, it takes each of its
attachment which is not already plain text and turns them into plain text. The
original attachment is left unchanged and a new attachment containing the plain
text is added.

The transformation into plain text is done depending on the file type of the
attachment using OCR and PDF text extraction.

Requirements
============

You need an IMAP account which a mailbox (folder) dedicated to your documents.
You can also use an own account for this. In this way, you can add new documents
easily by simply sending a mail to this account.

You need python installed, I used version 2.7. You also need [ImageMagick][im]
and [Tesseract][tess] installed in your PATH for the OCR jobs.

   [im]: http://www.imagemagick.org
   [tess]: http://code.google.com/p/tesseract-ocr/

Installation
===========

The most recent version is checked in at the [git-repository][gitrepo]. It uses
[git sub modules][gitsubmodules] to include external libraries. For this reason
you must download these sub modules after you have downloaded this repository.

    git clone https://github.com/theomega/IMAP_DMS.git
    cd IMAP_DMS
    git submodule init
    git submodule update

   [gitrepo]: https://github.com/theomega/IMAP_DMS
   [gitsubmodules]: http://git-scm.com/book/en/Git-Tools-Submodules

Usage
=====

   1. Create a configuration file: Have a look at the example
      `imap_dms.cfg.example`. You can find the available configuration options
      in the `imap_dms.defaults` file. Do not modify the defaults file but
      instead overwrite the setting which you need in the configuration.
   2. Run `processMails.py [configurationfile]` from the command line to see if
      everything works as expected
   3. Add a cronjob which runs `processMails.py` periodically.

The script can either run on your client machine or if possible directly on the
mail server. The later should be preferred as the documents do not have to be
downloaded to the client and later uploaded again.

Features
========

   - You can modify the behaviour of the script for each message individually by
     using different receivers. If for example `docs@domain.tld` gets delivered
     to the `check_folder` from the configuration, the script OCRs each
     attachment. If you instead write an email to `docs+noocr@domain.tld`, the
     message still gets delivered to the same folder, but the script does not do
     any OCR but instead only extracts the text from PDFs.
   - Tesseract, the OCR Engine used by this script can not auto detect the
     language which should be used. For this reason, there is a default language
     in the configuration. If you need to index a single document in a different
     language, simply send the email to `docs+languagecode@domain.tld`. For
     example for a french document use `docs+fra@domain.tld`. The language codes
     are those of the ISO 639-2 standard.


External Libraries
==================

This script uses the excellent [sh][shrepo] library for the execution of shell
commands. This library was written by [Andrew Moffat][amoffat] and is under an
MIT licence.


   [shrepo]: https://github.com/amoffat/sh
   [amoffat]: https://github.com/amoffat

To Do / Open Questions
====================

   - A script which adds pages from a scanner or a PDF directly (either by
     sending an email to the account or by directly appending to the IMAP
     folder) should be written. This script can help with the correct selection
     of the title, time stamp and tags.
   - Running the script as a cron job is not an ideal solution. Perhaps using a
     `procmail` script can be used here to synchronously handle incoming
     messages.
   - The script has not been tested on gmail. As Google provides nearly
     unlimited space, it could serve as an ideal place for document storage (if
     you have no privacy concerns).
   - The script is not tested very well, I could destroy everything....
   - It is not clear how portable the script is in terms of python versions and
     application versions.
   - Check if other OCR tools would be better suitable for this job.
