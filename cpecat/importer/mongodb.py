# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#
import cpecat.settings as settings
from pymongo import MongoClient

client = MongoClient(
    settings.DATABASES['mongodb']["HOST"],
    settings.DATABASES['mongodb']["PORT"]
)
db = client[settings.DATABASES['mongodb']['DATABASE']]
if settings.DATABASES['mongodb']["USERNAME"]:
    db.authenticate(
        settings.DATABASES['mongodb']["USERNAME"],
        settings.DATABASES['mongodb']["PASSWORD"]
    )


