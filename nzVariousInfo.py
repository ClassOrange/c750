# -*- coding: utf-8 -*-

import pprint
import re
import os
import xml.etree.ElementTree as ET
import operator
from collections import defaultdict

#%% Just declaring some variables for my working data files

myMap = 'Christchurch.xml'         
mySample = 'sample.xml'

#%% Get file size and divide by 1048576 in order to convert to MB

def filesize(file):
    return (os.path.getsize(myMap) / 1048576)

print('Christchurch OpenMap file is', format(filesize(myMap), 'n'), 'MB')

#%% Count the tags in order to find out 2nd level element frequencies

counts = {}
for event, element in ET.iterparse(myMap):
    counts[element.tag] = counts.get(element.tag, 0) + 1
    element_count = sorted(counts.items(), key=operator.itemgetter(1))
    print('The frequency of each 2nd level category:', counts)

#%%

unique_uid = set()
for event, element in ET.iterparse(myMap):
    if 'uid' in element.attrib:
        unique_uid.add(element.attrib['uid'])

print('Number of unique contributors:', len(unique_uid))

#%% Method to find the distinct count and values of the various k tag categories

k_tags = set()
for event, element in ET.iterparse(myMap):
    if 'k' in element.attrib:
        k_tags.add(element.attrib['k'])
print('Number of distinct k tag values:', len(k_tags), "\n", k_tags)

#%% Finds invalid (or forgotten) road suffixes

# Make the data file accessible for the rest of the code to use
open_data = open(myMap, 'r')

# Find road suffixes (road, street, avenue, etc) that don't match expectations
road_type_f = re.compile(r'\b\S+.?$', re.I)
road_types = defaultdict(set)

# List of many common road suffixes so we can set everything up to ignore them and only
# find potential problems
expected = ['Street', 'Avenue', 'Lane', 'Way', 'Boulevard', 'Drive',
            'Court', 'Place', 'Square', 'Road', 'Trail', 'Parkway',
            'Commons', 'North', 'South', 'East', 'West']

# Compile stuff like 'St.' and 'Rd' and whatnot, ignoring suffixes found in the expected
# list and default dictionary 

def check_road_types(road_types, road_name):
    m = road_type_f.search(road_name)
    if m:
        road_type = m.group()
        if road_type not in expected:
            road_types[road_type].add(road_name)

# Setting up and formatting to display the results

def print_road_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print('%s: %d' % (k, v))


def is_street_name(elem):
    return (elem.attrib['k'] == 'addr:street')


def audit():
    for event, elem in ET.iterparse(myMap, events=('start',)):
        if elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_street_name(tag):
                    check_road_types(road_types, tag.attrib['v'])
    pprint.pprint(dict(road_types))
    
#%% Run the previous stuff
audit()

#%% First chunk displays users as well as user count

def dist_users(myMap):
    users = set()
    for event, element in ET.iterparse(myMap):
        if element.tag in ("node","way","relation"):
            user = element.attrib['user']
            #print user
            users.add(user)
    print(users, "\nTotal count of users:", len(users))
    
dist_users(myMap)

#%% Just how to set/check info related to ElementTree basics

tree = ET.parse(mySample)
root = tree.getroot()

print(root)
print(root.tag)
print(root.attrib)