# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 20:20:47 2021

@author: Cindy
"""

import csv
import codecs
import re
import xml.etree.ElementTree as ET

#%% Variables to easily reference necessary files as well as map their
# columns properly

myMap = 'Christchurch.xml'

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']


#%% References and replacements used in cleaning street types

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

expected = ['Street', 'Avenue', 'Lane', 'Way', 'Boulevard', 'Drive',
            'Court', 'Place', 'Square', 'Road', 'Trail', 'Parkway',
            'Commons', 'North', 'South', 'East', 'West']

mapping = { "St": "Street",
            "St.": "Street",
            "street": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Boulavard": "Boulevard",
            "Rd": "Road",
            "Rd.": "Road",
            "RD": "Road",
            "Pl": "Place",
            "Pl.": "Place",
            "PKWY": "Parkway",
            "Pkwy": "Parkway",
            "Ln": "Lane",
            "Ln.": "Lane",
            "Dr": "Drive",
            "Dr.": "Drive"
            }

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#%%
 
# Only grab node, way, or relation elements         
def get_element(osm_file, tags=('node', 'way', 'relation')):
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# Enable processing of unicode for the csv files
class UnicodeDictWriter(csv.DictWriter, object):
    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k : v for k, v in row.items()
        })
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def update_street(name, mapping):
    street=street_type_re.search(name).group()
    name=name.replace(street, mapping[street])
    return name

# Replaces values and keys with cleaned ones, based on the other functions
def clean_element(tag_value, tag_key):
    
# Updates the street type if it's NOT in the expected list and IS in the
# list of automatic replacements     
    if tag_key=='street':
        street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
        full_addr=tag_value
        m = street_type_re.search(full_addr)
        if m:
            street_type = m.group() # group() returns string matched by the RE
            if street_type not in expected:
                if street_type in mapping:
                    tag_value=update_street(full_addr, mapping)
    return tag_value
                             
# Clean and shape node or way element to dict

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
   
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = [] # tags don't need any distinct treatment between nodes & ways
   
# Allows the splitting of child elements based on character location,
# so elements that were "doubled-up" so to speak can separate before being
# written to a csv (for nodes first and then ways)
    if element.tag=='node':
        for primary in element.iter():
            for i in node_attr_fields: 
                if i in primary.attrib: 
                    node_attribs[i]=primary.attrib[i]
        if len(element)!=0:
            for j in range(0, len(element)): 
                childelem=element[j]
                tag={}
                if not problem_chars.search(childelem.attrib['k']):
                    tag["id"]=element.attrib["id"]
                    tag["type"]=default_tag_type
                    tag['value']=childelem.attrib['v']
                    if ':' in childelem.attrib['k']:
                        k_and_v=childelem.attrib['k'].split(':',1)
                        tag["type"]=k_and_v[0]
                        tag["key"]=k_and_v[1]
                        if tag["type"]=='addr':
                            tag["value"]=clean_element(tag["value"],tag["key"])
                    else:
                        tag["key"]=childelem.attrib['k']
                        if tag["type"]=='addr':
                            print(tag['value'], tag["key"])
                            tag["value"]=clean_element(tag["value"],tag["key"])
                tags.append(tag)
                
        return ({'node': node_attribs, 'node_tags': tags})            
                                
    elif element.tag=='way':
        for primary in element.iter():
            for i in way_attr_fields: 
                if i in primary.attrib: 
                    way_attribs[i]=primary.attrib[i]   
        
        if len(element)!=0: 
            for j in range(0, len(element)): 
                childelem=element[j]
                tag={}
                if childelem.tag=='tag':
                    if not problem_chars.search(childelem.attrib['k']):
                        tag["id"]=element.attrib["id"]
                        tag["type"]=default_tag_type
                        tag["value"]=childelem.attrib['v']
                        if ':' in childelem.attrib['k']:
                            k_and_v=childelem.attrib['k'].split(':',1)
                            tag["key"]=k_and_v[1]
                            tag["type"]=k_and_v[0]
                            if tag["type"]=='addr':
                                tag["value"]=clean_element(tag["value"],tag["key"])
                        else:
                            tag["key"]=childelem.attrib['k']
                            if tag["type"]=='addr':
                                tag["value"]=clean_element(tag["value"],tag["key"])
                    tags.append(tag)
                    
                elif childelem.tag=='nd':
                    way_node={}
                    way_node['id']=element.attrib['id'] 
                    way_node['node_id']=childelem.attrib['ref']
                    way_node['position']=j
                    way_nodes.append(way_node)
                    
        return ({'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags})
    
#%% The function that takes this entire document and makes it all work together
# in order to create the csv files and write all specified data to them

def process_map(file_in):
    with codecs.open(NODES_PATH, 'w', encoding='utf-8') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w', encoding='utf-8') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w', encoding='utf-8') as ways_file,         codecs.open(WAY_NODES_PATH, 'w', encoding='utf-8') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w', encoding='utf-8') as way_tags_file:
                
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
    
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
                    
process_map(myMap)