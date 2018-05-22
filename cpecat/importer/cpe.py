# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#
import sys
import os
import cpecat.settings as settings

from gzip import GzipFile
from io import BytesIO
from zipfile import ZipFile

from pymongo import TEXT
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import urllib.request as req
from urllib.error import URLError
import progressbar
from cpecat.importer.mongodb import db


class CPEImporter:
    def __init__(self):
        self.db = db

    def c(self, collection_name):  # get a collection from the database creating it if it doesn't exist yet
        if collection_name not in self.db.collection_names():
            self.db.create_collection(collection_name)

        return db[collection_name]

    def load_from_remote(self, source):
        try:
            f, s = self.getFile(settings.CPE_SOURCE, source)
            return f, s
        except Exception as e:
            print(Exception, e)
            sys.exit("Cannot open url %s. Bad URL or not connected to the internet?" % (settings.CPE_SOURCE))

    def load_from_local(self, source):
        try:
            filename = settings.CPE_SOURCE.split('/')[-1]
            z = ZipFile(source + '/' + filename, 'r')
            fname = z.namelist()[0]
            size = z.getinfo(fname).file_size
            f = z.open(fname)
            return f, size
        except FileNotFoundError as e:
            print(FileNotFoundError, e)
            print("Downloading from online source...")
            return self.load_from_remote(source)

    def do_import(self, source, download=True):
        # info = CollectionInfo()
        # i = info.getLastModified('cpe')
        self.reset_collections()

        parser = make_parser(['xml.sax.IncrementalParser'])
        col = self.c("cpe")
        col.create_index('id')
        ch = self.CPEHandler(col)
        parser.setContentHandler(ch)

        if download:
            print("Downloading data...")
            f, size = self.load_from_remote(source)
        else:
            print("Opening from local source...")
            f, size = self.load_from_local(source)
            # last_modified = datetime(*f_info.date_time)

        # if i is not None:
        #     if last_modified == i:
        #         print("Already updated with the latest data.")
        #         return

        print("Updating database...")


        # parse xml and store in database
        bar = progressbar.ProgressBar(max_value=size)
        bar.start()
        buf = f.readline()
        progress = 0
        while len(buf) != 0:
            parser.feed(buf)
            progress += len(buf)
            bar.update(progress)
            buf = f.readline()
        bar.finish()

        self.reindex()


        # for x in bar(ch.cpe):
        #     x['id'] = x.pop('cpe23')
        #     x['title'] = x['title'][0]
        #     x['cpe_2_2'] = x.pop('name')
        #     if not x['references']: x.pop('references')
        #     col.update({'id': x['id']}, {'$set': x}, upsert=True)
        #
        # # update database info after successful program-run
        # # info.update('cpe', last_modified)
        #


    # def getInfo(collection):
    #     return sanitize(colINFO.find_one({"db": collection}))
    #
    # def getLastModified(collection):
    #     info = getInfo(collection)
    #     return info['last-modified'] if info else None

    def reindex(self):
        self.c("cpe").drop_indexes()
        print("Generating fulltext search index for cpe...")
        self.c("cpe").create_index(
            [("id", TEXT),
             ("title", TEXT),
             ("references", TEXT),
             ("cpe_2_2", TEXT)], name="fulltext_search"
        )
        print("...complete")
        
    def reset_collections(self):
        print("Resetting cpe collection...")
        self.db.drop_collection('cpe')
        # self.info.reset(self.get_type())

    def getFile(self, getfile, source, unpack=True):
        try:
            response = req.urlopen(getfile)
        except URLError as e:
            sys.exit(e)

        filepath = source + '/' + getfile.split('/')[-1]

        data = response
        save_file = open(filepath, 'wb')
        save_file.write(response.read())
        save_file.close()

        file = open(filepath, 'rb')
        size = 0
        # TODO: if data == text/plain; charset=utf-8, read and decode
        if unpack:
            # if 'gzip' in response.info().get('Content-Type'):
            #     buf = BytesIO(file.read())
            #     data = GzipFile(fileobj=buf)
            # elif 'bzip2' in response.info().get('Content-Type'):
            #     data = BytesIO(bz2.decompress(response.read()))
            if 'zip' in response.info().get('Content-Type'):
                fzip = ZipFile(BytesIO(file.read()), 'r')
                filename = fzip.namelist()[0]
                size = fzip.getinfo(filename).file_size
                if len(fzip.namelist()) > 0:
                    data = BytesIO(fzip.read(filename))
        file.close()

        return data, size


    # CPE SAX content handler
    class CPEHandler(ContentHandler):
        def __init__(self, col):
            self.col = col
            self.cpe = None
            self.titletag = False
            self.referencestag = False
            self.referencetag = False

        def startElement(self, name, attrs):
            if name == 'cpe-item':
                self.name = attrs.get('name')
                self.cpe = {'id': '', 'title': [], 'references': [], 'cpe_2_2': self.name}
            elif name == 'title':
                if attrs.get('xml:lang') == 'en-US':
                    self.titletag = True
                    self.title = ""
            elif name == 'cpe-23:cpe23-item':
                self.cpe['id'] = attrs.get('name')
            elif name == 'references':
                self.referencestag = True
            elif name == 'reference':
                self.referencetag = True
                self.referencetitle = ""
                self.href = attrs.get('href')

        def characters(self, ch):
            if self.titletag:
                self.title += ch
            elif self.referencetag:
                self.referencetitle += ch

        def endElement(self, name):
            if name == 'cpe-item':
                if not self.cpe['references']:
                    self.cpe.pop('references')
                self.col.update({'id': self.cpe['id']}, {'$set': self.cpe}, upsert=True)
                self.cpe = None
            elif name == 'title':
                self.titletag = False
                self.cpe['title'] = self.title.rstrip()
            elif name == 'references':
                self.referencestag = False
            elif name == 'reference':
                self.cpe['references'].append({'reference_title': self.referencetitle, 'href': self.href})
                self.referencetag = False
                self.referencetitle = None
                self.href = None