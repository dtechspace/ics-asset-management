# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#
CPE_SOURCE = "https://static.nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"

DATABASES = {
    'mongodb': {
        'DATABASE': 'cpecat',
        'HOST': 'localhost',
        'PORT': 27017,
        'USERNAME': None,
        'PASSWORD': None
    }
}