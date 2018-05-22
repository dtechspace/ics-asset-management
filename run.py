# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#
import argparse
from cpecat.importer.cpe import CPEImporter
from cpecat.categorize import Categorize

import progressbar, time

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')

    # subparser for import
    cpe_import = subparsers.add_parser('import')
    cpe_import.add_argument("-s", "--source", dest="source", help="CPE Source")
    cpe_import.add_argument("-dl", "--download", dest="download", help="import cpe from remote source", action="store_true")

    # subparser for categorize
    categorize = subparsers.add_parser('categorize')
    categorize.add_argument('-f', '--force', dest="force", help='Drop cpe categories collection before re-categorizing', action="store_true")

    args = parser.parse_args()

    if args.subcommand == 'import':
        CPEImporter().do_import(source=args.source or "data", download=args.download)
    elif args.subcommand == 'categorize':
        if args.force:
            c = Categorize(reset=True)
        else:
            c = Categorize()

        # c.vendor_check_uncategorized()

        print('- Categorizing Hardware')
        c.categorize_hardware()
        print('- Categorizing Operating Systems')
        c.categorize_os()
        print('- Categorizing Applications')
        c.categorize_applications()
        c.statistics()
        print('done')

if __name__ == "__main__": main()
