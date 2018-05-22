#!/bin/bash
# Copyright © 2018, D-Tech, LLC, All Rights Reserved. 
# Disclaimer: This software is provided "AS IS" without warrantees.  
# D-Tech, LLC has no oblication to provide any maintainence, update 
# or support for this software.  Under no circumstances shall D-Tech,  
# LLC be liable to any parties for direct, indirect, special, incidential,
# or consequential damages, arising out of the use of this software
# and related data and documentation.
#

#install mongodb, python3, and git
brew install mongodb python3 git
brew tap homebrew/services
brew services start mongodb

#fetch latest code, configure python venv
git fetch && git pull
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

