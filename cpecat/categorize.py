# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#
from cpecat.importer.mongodb import db
import re
from xml.etree import ElementTree
from decimal import Decimal
from pprint import pprint


class Categorize:

    def __init__(self, reset=False):
        """
        This creates the collection and inserts the cpe category documents if the collection doesn't exist.
        Based off of asset-taxonomy-v1.1.xml but the dictionary is unwinded a couple of layers for more clarity and ease
        of use in the mongodb.
        """
        if reset:
            print('Dropping cpe_categories collection')
            db.drop_collection('cpe_categories')
        self.cpes = db.get_collection('cpe')
        self.initial = False
        if 'cpe_categories' not in db.collection_names():
            db.create_collection('cpe_categories')
            self.initial = True
        self.parse_taxonomy('data/asset-taxonomy-v1.1.xml')
        self.categories = db.get_collection('cpe_categories')

    def parse_taxonomy(self, xml_file):
        """
        Parses the asset-taxonomy file and creates documents based on the three basic cpe identifiers
        cpe:2.3:(a/o/h)

        All of the keywords apart from the cpe identifiers should go to the leaf nodes.
        :param xml_file: location of asset taxonomy file
        """
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
        hardware = {}
        os = {}
        application = {}
        it_asset = root[0][0]
        hardware_asset = it_asset[0]
        os_asset = it_asset[1][0]
        application_asset = it_asset[1][1]

        self.taxonomy_to_dict(hardware_asset, hardware)
        self.taxonomy_to_dict(os_asset, os)
        self.taxonomy_to_dict(application_asset, application)
        hardware = hardware['Hardware']
        hardware['id'] = 'hardware'
        os = os['Operating-System']
        os['id'] = 'os'
        application = application['Application']
        application['id'] = 'application'
        insert_list = [hardware, os, application]
        if not self.initial:
            mongo_hd = db.get_collection('cpe_categories').find_one({'id': 'hardware'})
            mongo_os = db.get_collection('cpe_categories').find_one({'id': 'os'})
            mongo_app = db.get_collection('cpe_categories').find_one({'id': 'application'})
            hardware_merged = self.merge_existing(mongo_hd, hardware)  # this part combines what currently exists in the mongodb with the new
            os_merged = self.merge_existing(mongo_os, os)              # keywords and categories from the updated taxonomy.
            application_merged = self.merge_existing(mongo_app, application)
            insert_list = [hardware_merged, os_merged, application_merged]

        for elem in insert_list:
            print('Updating %s structure' % elem['id'])
            db.get_collection('cpe_categories').update({'id': elem['id']}, {'$set': elem}, upsert=True)
        print('')

    def taxonomy_to_dict(self, root, x):
        """
        recursive method to parse the asset taxonomy xml file.
        base case is if the node is a keyword node. If it is then it will append the keyword into a keyword list, or create a new one
        if it doesn't exist.
        recursive step goes to the next node. If node has no children then nothing happens.
        :param root: current node in the xml dom tree
        :param x: the dictionary variable that the xml dom tree is being converted into.
        """
        tag = root.tag.split('}')[-1]
        if tag == 'keyword':
            if 'keyword' in x.keys():
                x['keyword'].append(root.text)
            else:
                x['keyword'] = [root.text]
        elif tag == 'asset':
            x[root.attrib['name']] = {}
            # if 'asset' not in [f.tag.split('}')[-1] for f in list(root)]:
            #     x[root.attrib['name']]['cpe_list'] = []
            for child in root:
                self.taxonomy_to_dict(child, x[root.attrib['name']])
        else:
            raise ValueError("invalid tag: {}".format(tag))

    def merge_existing(self, a, b, path=None, override=False):
        """
        Merges b into a
        :param a: original
        :param b: new
        :param path: tracks location of recursive merge if there are conflict errors
        :param override: replace value in a if b exists
        :return: merged dictionary
        """
        if a is None:
            return b

        if path is None:
            path = []

        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge_existing(a[key], b[key], path + [str(key)], override)
                elif a[key] == b[key]:
                    pass
                elif isinstance(a[key], list) and isinstance(b[key], list):
                    a[key] = list(set().union(a[key], b[key]))
                elif override:
                    a[key] = b[key]
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    def categorize_hardware(self):
        """
        Puts all cpe:2.3:h matching cpe's into a list and then moves cpe's from that list to the individual leaf nodes if it matches.
        cpe's that aren't matched remain in the original cpe list.
        """
        hardware_doc = self.categories.find_one({'id': 'hardware'})

        # first time load all cpes with proper cpe identifier into a list saved into the category. All leafs pull from this list.
        if self.initial:
            keyword_list = hardware_doc['keyword']
            regx = re.compile(keyword_list[0], re.IGNORECASE)
            pipeline = [
                {'$match': {'id': regx}},
                {'$project': {'_id': 1, 'id': 1, 'title': 1}}
            ]
            full_hardware_list = list(self.cpes.aggregate(pipeline))

            self.categories.update_one(
                {'id': 'hardware'},
                {'$addToSet':
                    {
                        'cpe_list': {'$each': full_hardware_list}
                    }
                }
            )

        for k, v in hardware_doc.items():
            if isinstance(v, dict):
                self.dictionary_walk(v, [], 'hardware', k)
        print('')

    def categorize_os(self):
        os = self.categories.find_one({'id': 'os'})

        if self.initial:
            kwd = os['keyword']
            regx = re.compile(kwd[0], re.IGNORECASE)
            pipeline = [
                {'$match': {'id': regx}},
                {'$project': {'_id': 1, 'id': 1, 'title': 1}}
            ]
            full_os_list = list(self.cpes.aggregate(pipeline))

            self.categories.update_one(
                {'id': 'os'},
                {'$addToSet':
                    {
                        'cpe_list': {'$each': full_os_list}
                    }
                }
            )

        for k, v in os.items():
            if isinstance(v, dict):
                self.dictionary_walk(v, [], 'os', k)
        print('')

    def categorize_applications(self):
        application = self.categories.find_one({'id': 'application'})

        if self.initial:
            kwd = application['keyword']
            regx = re.compile(kwd[0], re.IGNORECASE)
            pipeline = [
                {'$match': {'id': regx}},
                {'$project': {'_id': 1, 'id': 1, 'title': 1}}
            ]
            full_application_list = list(self.cpes.aggregate(pipeline))

            self.categories.update_one(
                {'id': 'application'},
                {'$addToSet':
                    {
                        'cpe_list': {'$each': full_application_list}
                    }
                }
            )

        for k, v in application.items():
            if isinstance(v, dict):
                self.dictionary_walk(v, [], 'application', k)
        print('')

    def statistics(self):
        print('')
        hardware_doc = self.categories.find_one({'id': 'hardware'})
        os_doc = self.categories.find_one({'id': 'os'})
        application_doc = self.categories.find_one({'id': 'application'})
        h_total_cpes = self.cpes.find({'id': re.compile('^cpe:2.3:h', re.IGNORECASE)}).count()
        h_categorized_cpes = h_total_cpes - len(hardware_doc['cpe_list'])
        percent = Decimal(h_categorized_cpes) / Decimal(h_total_cpes)
        print('Total Hardware CPEs: %d    Total Categorized CPEs: %d    Percent: %f%%' % (h_total_cpes, h_categorized_cpes, percent * 100))

        o_total_cpes = self.cpes.find({'id': re.compile('^cpe:2.3:o', re.IGNORECASE)}).count()
        o_categorized_cpes = o_total_cpes - len(os_doc['cpe_list'])
        percent = Decimal(o_categorized_cpes) / Decimal(o_total_cpes)
        print('Total Operating System CPEs: %d    Total Categorized CPEs: %d    Percent: %f%%' % (o_total_cpes, o_categorized_cpes, percent * 100))

        a_total_cpes = self.cpes.find({'id': re.compile('^cpe:2.3:a', re.IGNORECASE)}).count()
        a_categorized_cpes = a_total_cpes - len(application_doc['cpe_list'])
        percent = Decimal(a_categorized_cpes) / Decimal(a_total_cpes)
        print('Total Application CPEs: %d    Total Categorized CPEs: %d    Percent: %f%%' % (a_total_cpes, a_categorized_cpes, percent * 100))

        final_total = h_total_cpes + o_total_cpes + a_total_cpes
        final_categorized = h_categorized_cpes + o_categorized_cpes + a_categorized_cpes
        final_percent = Decimal(final_categorized) / Decimal(final_total)
        print('Total CPEs: %d    Total Categorized: %d    Percent: %f%%' % (final_total, final_categorized, final_percent * 100))

    def dictionary_walk(self, root, regx_list, cpe_type, set_name):
        """
        Recursive method to traverse through the mongodb document and populate the leaf node cpe lists with the keywords saved into mongodb

        :param root: current node
        :param regx_list: the list that is put together based on the tree structure of the mongodb document.
        :param cpe_type: (hardware, os, application) so mongo knows which document to save the cpe list into
        :param set_name: this is a string that collects the names of keys to know where to save the final cpe_list.
        """
        print((set_name + 100*' ')[:100], end='\r')
        if 'keyword' in root.keys():
            new_regx = [re.compile(r, re.IGNORECASE) for r in root['keyword']]
            regx_list.extend(new_regx)

        search_title = True
        # if 'Frameworks' in set_name:
        #     print('Searching in title')
        #     search_title = True

        is_leaf = True
        for v in root.values():
            if isinstance(v, dict):
                is_leaf = False

        if is_leaf:
            regx_list.append(re.compile(set_name.split('.')[-1], re.IGNORECASE))
            cpes = self.regx_aggregator(regx_list[:], cpe_type, search_title)
            set_name += '.cpe_list'

            # insert cpes into leaf list
            self.categories.update_one(
                {'id': cpe_type},
                {'$addToSet':
                    {
                        set_name: {'$each': cpes}
                    }
                }
            )

            # remove cpes from base pool
            self.categories.update_one(
                {'id': cpe_type},
                {'$pullAll':
                     {
                         'cpe_list': cpes
                     }
                }
            )
        else:
            for k, v in root.items():
                if isinstance(v, dict):
                    self.dictionary_walk(v, regx_list[:], cpe_type, set_name + '.' + k)

    def vendor_check(self):
        """
        quick sort method to help find some keywords.
        """
        vendors = {}
        cursor = db.get_collection('cpe').find({'id': re.compile('^cpe.2.3:a', re.IGNORECASE)})
        for document in cursor:
            segmented_id = document.get('id').split(':')
            if len(segmented_id) >= 4:
                vendor = segmented_id[3]
            else:
                vendor = '-'

            if vendor in vendors.keys():
                vendors[vendor] += 1
            else:
                vendors[vendor] = 1

        self.categories.insert(vendors, check_keys=False)

    def vendor_check_uncategorized(self):
        count = {}
        application_doc = self.categories.find_one({'id': 'application'})
        for cpe in application_doc['cpe_list']:
            segmented_id = cpe.get('id').split(':')
            if len(segmented_id) >= 4:
                vendor = segmented_id[3]
            else:
                vendor = '-'

            if vendor in count.keys():
                count[vendor] += 1
            else:
                count[vendor] = 1

        self.categories.insert(count, check_keys=False)

    def regx_aggregator(self, regx_list, cpe_type, search_title):
        """
        takes a list of regular expressions and creates an aggregation from the base cpe list
        list elements get searched in both title and id

        Considering using a better search method other than regular expressions because it's slow
        :param regx_list: list of regular expressions
        :return: list of cpe's that match the regular expression. Each element in the list is a dictionary with oid, title, and id keys
        """
        pipeline = [
            {'$match': {'id': cpe_type}},
            {'$project': {'cpe_list': 1}},
            {'$unwind': '$cpe_list'}
        ]

        if len(regx_list) != 0:
            if search_title:
                matching = [
                    {'cpe_list.id': {'$in': regx_list}},
                    {'cpe_list.title': {'$in': regx_list}}
                ]
                pipeline.append({'$match': {'$or': matching}})
            else:
                pipeline.append({'$match': {'cpe_list.id': {'$in': regx_list}}})

        pipeline.append({'$project': {'_id': '$cpe_list._id', 'id': '$cpe_list.id', 'title': '$cpe_list.title'}})
        bbb = list(self.categories.aggregate(pipeline))

        return bbb

