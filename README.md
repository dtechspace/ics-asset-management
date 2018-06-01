# ICS Asset Management (ICSAM)
## What is ICSAM?
This project contains the ICSAM data model and software tools for asset management for industrial control systems (ICS).  The goal of the ICSAM is to develop a common asset management framework to support a range of asset management related applications in ICS (e.g. supply-chain management, cybersecurity vulnerability management, and risk analytics).  As an open source project, our intent is to create a set of interoperable ICSAM data models and tools for the ICS industry and beyond.

The initial version of ICSAM (version 0.9) contains a set of asset management data models and the application for classifying Common Platform Enumeration (CPE) dictionary entries published by the National Vulnerability Database (NVD).  See https://nvd.nist.gov/products/cpe for more details about CPE. 

## The Project Structure and Content
The current ICSAM project contains the data models of ICSAM (in XML Schema format), the original CPE dictionary file (CPE version 2.3), and the Python script.

* ics-asset-management
  * cpecat - The directory of the python module for CPE categorization 
  * data - Contains the CPE input file and the asset taxonomy definition file 
    * xsd - The ICSAM data model (XML schema files)
      * asset-management-0.9.1.xml - Defines XML elements and data types for IT and OT assets
      * shared-datatypes_0.9.xsd - Defines common data types and utility elements
      * asset-taxonomy-schema_0.9.xsd - Defines the asset taxonomy structure
  * README.md - This file
  * LICENSE - The Apache 2.0 open source license file
  * requirements.txt - The requirement file for setting up the Python virtual environment
  * run.py - The main Python script file
  * setup_mac.sh - The bash shell script to set up the MongoDB database and the Python virtual environment on Mac OS.

## Setup and Usage
You need to setup the MongoDB and the Python virtual environment before running the categorization script.  A sample setup script for the Mac OS is defined in setup_mac.sh.  You may want to customize it for your own OS and your workspace.

Once you have MongoDB and Python virtual environment established, you can start the CPE categorization process in your virtual environment.

1.  Populating the MongoDB with the CPE dictionary data

```
python run.py import [-s or --source SOURCE] [-dl ?download]
	-s SOURCE specifies the directory where the cpe zip file is located. If no source is supplied, it defaults to the data/ directory
	-dl forces a download from the NVD web site.  If starting without -dl and there is no file found in the source destination, 
	the program will automatically pull the CPE data from the NVD web site, as well as save it locally in the default directory.
```

2.  Categorizing CPE entries

```    
python run.py categorize [-f or --force]
	-f drops existing CPE categorized collection in MongoDB before rerunning the categorization script
```

3.  Viewing categorized CPE entries

We recommend using a third party mongodb database viewer such as Robo 3T to view the categorized CPE collection.  The three documents found in the cpe_categories collection are the Hardware, Operating System, and Application categories.  CPE entries will be saved into a hierarchical format mirroring the XML asset taxonomy.  Uncategorized CPE entries will be stored in the cpe_list found in the root of each document.  Categorized entries will be found in the leaf nodes alongside a list of keywords used to aggregate the CPE entries.

## Why ICSAM?

Currently, there is no industry-wide data models or standards that support ICS-specific asset management functions.  The existing data models for ICSAM are either vendor-specific or tailored to specific database or tool implementation.  As a results, asset data are confined to specific applications or organizations, resulting data redundancies across applications and data siloes across the enterprise.  There is an emerging need to develop a common asset management standard for the ICS industry.

The direct motivation behind this project is the need of an asset management standard for cybersecurity risk assessment in ICS.  We initially followed the Asset Identification (AI) data model published by the National Institute of Standards and Technology (NIST) as part of the Security Content Automation Protocol (SCAP) standard suite (https://csrc.nist.gov/projects/security-content-automation-protocol).  However, the AI data standard is designed primarily for general digital assets in an IT environment, and not for ICS assets in an integrated IT/OT environment.  In addition, it lacks the necessary data representation for advanced computing and control architectures (e.g. the representation of hypervisor and virtual machine guests), and the representation of composite relationships among software components).  The asset management data model defined in this project leverages and extends the NIST AI data model to include additional elements and attributes to support cybersecurity vulnerability discovery and risk quantification.

## ICS Asset Taxonomy

A taxonomy is essentially a classification scheme that groups a set of entities into different categories.  An asset taxonomy will be necessary to enable ICS asset classification for different data analysis purposes.  For instance, some enterprise users or cybersecurity analysts may be interested in knowing the highest cybersecurity vulnerability or risk among different asset categories.  Unfortunately, most asset taxonomy definitions are vendor specific (e.g. CDW?s sales catalog of hardware and software).  There is no common asset classification in the ICS industry (or IT industry in general). 

The asset taxonomy defined for ICS assets is our initial attempt to develop a vendor-neutral and extensible categorization scheme that can be used to represent the latest IT and OT technologies.  The intermediate use of this asset taxonomy is to categories the Common Platform Enumeration (CPE) entries for enabling detailed vulnerability assessment on various IT and OT assets in an asset pool or network.

## CPE Categorization
The Common Platform Enumeration (CPE) is another data standard in SCAP to provide unique identifiers for various hardware configurations, software applications and operating systems.  There are over 120,000 CPE entries currently defined in the NVD.  They are grouped by product vendors under three main categories: hardware, operating system, and application.   CPE is categorized by vendors, and does not follow any asset taxonomy.  To categorize CPE automatically based on the proposed asset taxonomy, a Python program is implemented.  It goes through every entry in the official CPE dictionary and assign a category to the entry based on keywords or asset definitions in the asset taxonomy.

Because of the large data volume and multiple iterations the CPE categorization needs to handle, the Python program uses MongoDB (https://www.mongodb.com), an open source NoSQL database, for storing the CPE entries and the categorization collections.  The collection results can then be easily exported to JSON or XML files using MongoDB functions.  

## Current Status and Development Roadmap
The current approach to CPE categorization is solely based on the asset taxonomy with a  hierarchy of asset types and keywords that are created manually.  Using the current taxonomy file, we have successfully categorized over 70% of the entire CPE (excluding the deprecated CPE entries).  There could be some ambiguities and discrepancies in terms of how an asset should be categorized (e.g. an asset may belong to multiple categories).  The current categorization script doesn't have such options and only selects the first match to assign asset categories in the process.

The future development plan includes extending the taxonomy definitions to reach 100% CPE categorization, improving the efficiency and performance of the categorization script (e.g. running categorization of hardware, OS, and applications concurrently), and implementing visualization functions to demonstrates the taxonomical relationships among various ICS assets.

For comments and suggestions, please send email to contact at dtechspace dot com.

 

