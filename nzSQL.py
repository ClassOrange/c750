# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 21:03:38 2021

@author: Cindy
"""

import pandas
import sqlite3 as s3
from sqlite3 import Error

#%% Just declaring some variables for my working data files

myMap = 'Christchurch.xml'
mySample = 'sample.xml'
nodesFile = 'nodes.csv'
nodesTagsFile = 'nodes_tags.csv'
waysNodesFile = 'ways_nodes.csv'
waysTagsFile = 'ways_tags.csv'
waysFile = 'ways.csv'
DB = 'ChristchurchDB.sqlite3'

#%%
def sql_connection():
    try:
        con = s3.connect(DB)
        return con 
    except Error:
        print(Error)
def sql_table(con):
    cursorObj = con.cursor()
    cursorObj.execute("CREATE TABLE ways_tags(id integer PRIMARY KEY, key text, value text, type text)")
    con.commit()

con = sql_connection()
sql_table(con)

#%% How to select

# cursorObj.execute('SELECT id, name FROM employees')

#%% list tables

con = s3.connect(DB)
def sql_fetch(con):
    cursorObj = con.cursor()
    cursorObj.execute('SELECT name from sqlite_master where type="table"')
    print(cursorObj.fetchall())
    
sql_fetch(con)

#%% creating a pandas df for each csv, then using that to build the sql tables

con = s3.connect(DB)

pdNodes = pandas.read_csv(nodesFile)
pdNodes.to_sql('nodes', con, if_exists = 'replace', index = False) 

pdNodesTags = pandas.read_csv(nodesTagsFile)
pdNodesTags.to_sql('nodes_tags', con, if_exists = 'replace', index = False)

pdWaysNodes = pandas.read_csv(waysNodesFile)
pdWaysNodes.to_sql('ways_nodes', con, if_exists = 'replace', index = False)

pdWaysTags = pandas.read_csv(waysTagsFile)
pdWaysTags.to_sql('ways_tags', con, if_exists = 'replace', index = False)

pdWays = pandas.read_csv(waysFile)
pdWays.to_sql('ways', con, if_exists = 'replace', index = False)

#%% find upper and lower for lat/long

pdNodes = pandas.read_csv(nodesFile)
minValues = pdNodes[['lat', 'lon']].min()
maxValues = pdNodes[['lat', 'lon']].max()
print('minimum values:\n', minValues,
      '\nmaximum values:\n', maxValues)

#%% selecting from a table

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT type, count(type) FROM nodes_tags GROUP BY type ORDER BY count(type) desc LIMIT 20'):
    print(row)
con.close()

#%% pelican 3 and zebra 36

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT value, count(value) FROM nodes_tags WHERE key="crossing_ref" GROUP BY value'):
    print(row)
con.close()

#%%

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT key, count(key) FROM nodes_tags GROUP BY key ORDER BY count(key) desc LIMIT 50'):
    print(row)
con.close()

#%%

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT value, count(value) FROM nodes_tags WHERE key="entrance" GROUP BY value'):
    print(row)
con.close()

#%%

# keys 'access' and 'entrance' in nodes_tags seem to be mixed up; there's a lot of 'yes' in entrance that should be in access

#%%

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT value, count(value) FROM nodes_tags WHERE key="amenity" GROUP BY value ORDER BY count(value)'):
    print(row)
con.close()

#%% Column information about each table

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT * FROM sqlite_master'):
    print(row, '\n')
con.close()

#%% List of all distinct users between nodes and ways

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT DISTINCT n.user FROM nodes n JOIN ways w on n.user = w.user'):
    print(row, '\n')
con.close()

#%% Count of distinct users between nodes and ways

con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT count(DISTINCT n.user) FROM nodes n JOIN ways w on n.user = w.user'):
    print(row, '\n')
con.close()









