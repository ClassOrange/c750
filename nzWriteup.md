# Open Street Map Data
Open Street Map (OSM) is a mapping project consisting of data populated by users around the world. Data generated and compiled by the general populace can be pretty beneficial, as the number of sources can be dramatically high. On the other hand, people make all sorts of mistakes; increasing the number of sources also likely increases the *types* of mistakes, making it more difficult to pinpoint all of them.

## Location: Christchurch, New Zealand
While I have no personal connection to New Zealand, I've been nursing a dream of living there since at least first grade. New Zealand is pretty small and Christchurch seems to be scaled down (with regard to an average city's size) to match, but it still offers plenty of data to fulfill the guidelines of this project.
## Data

### Obtaining the Data
The initial data was retrieved as an OSM/XML file from Open Street Map through the Overpass API using a simple query:
```python
(node(-43.608199, 172.488105, -43.401101, 172.754500;<;);out meta;
```
Side note: I later found out a hyperlink could simplify that process a bit; replacing the lat/lon values (found after drawing a bounding box in Open Street Map) in the below link will allow you to create and download the file by simply following the link.
```
http://overpass-api.de/api/map?bbox=172.488105,-43.608199,172.754500,-43.401101
```

### Data Details
The file (I changed the aptly named 'map' to 'Christchurch.xml') size can obviously be found by inspecting the file's properties, but it can also be determined through Python code; the reason I've got `/ 1048576` in the code is to convert the result from bytes to MB:
```python
def filesize(file):
    return (os.path.getsize(myMap) / 1048576)
print('Christchurch OpenMap file is', format(filesize(myMap), 'n'), 'MB')
```
Output is shown as `Christchurch OpenMap file is 240.931 MB`.

Frequencies of the data-determined (as opposed to outer-most level such as 'osm' with a count of 1) elements were determined with the following code:
```python
counts = {}
for event, element in ET.iterparse(myMap):
    if element.tag in ('node', 'way', 'relation', 'member', 'nd', 'tag'):
        counts[element.tag] = counts.get(element.tag, 0) + 1
element_count = sorted(counts.items(), key=operator.itemgetter(1))
print('The frequency of some main elements:\n')
element_count
```
With an output of:
```
The frequency of some main elements:
[('relation', 1804),
 ('member', 17644),
 ('way', 104541),
 ('nd', 1008116),
 ('node', 1009610),
 ('tag', 1189511)]
 ```
 For some reason, the count of unique users contributing to Christchurch's data surprised me; it was much higher than I'd thought it would be. The output of my query on the matter was `Number of unique contributors: 863`, so I understand that it's still under 1,000 and in reality it's not a large number but I found it to be an encouraging one. I'd maybe pessimistically guessed the number would only be about a quarter of that.
```python
unique_uid = set()
for event, element in ET.iterparse(myMap):
    if 'uid' in element.attrib:
        unique_uid.add(element.attrib['uid'])
print('Number of unique contributors:', len(unique_uid))
```

### Conversion
While some of my issues with the data were clear more immediately, others were discovered or clarified after setting up the data to work within SQL, so I'd like to cover that process before going into detail in the problems section. The programmatic cleaning aspect was related to street types; that code does run in conjunction with the creation and population of five CSV files and that can all be found in the submission's [nzCreateCSV](https://github.com/ClassOrange/c750/blob/main/nzCreateCSV.py) file.

After importing the `pandas` and `sqlite3` modules, the creation and population of my five SQL tables was shockingly simple. The process was just creating a dataframe for each csv then using that dataframe to do the rest all in a single line:
```python
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
```

### Database Details
Querying the database using sqlite3 involves first opening a connection to the database and creating a connection cursor
```
ChristchurchDB.sqlite3...230MB
```
```python
con = s3.connect(DB)
cur = con.cursor()
```

#### Distinct User Count
```python
for row in cur.execute('SELECT count(DISTINCT n.user) FROM nodes n JOIN ways w on n.user = w.user'):
    print(row)
```
The outcome is `482`

#### Count of Nodes & Ways
```python
for row in cur.execute('SELECT count(id) FROM nodes'):
    print(row)
```
Result: `1009610`
```python
for row in cur.execute('SELECT count(id) FROM ways'):
    print(row)
```
Result: `104541`

#### Various Info I Find Interesting
```python
for row in cur.execute('SELECT value, count(value) FROM nodes_tags WHERE key="amenity"
                        GROUP BY value ORDER BY count(value) desc LIMIT 10'):
    print(row)
```
The above code (results below) is meant to search through the nodes_tags table and return the value/counts of the most common 10 traits associated with the tag value 'amenity'. The results actually make me very curious about what constitutes 'fast_food' and what's considered a 'restaurant' but that's a more in-depth dive for another time.
```python
('bench', 450)
('restaurant', 211)
('fast_food', 189)
('cafe', 151)
('bicycle_parking', 149)
('toilets', 100)
('waste_basket', 99)
('drinking_water', 98)
('parking', 85)
('post_box', 82)
```

Now honestly for the below (finding the values associated with `crossing_ref`), I was immediately very confused, as initially upon reading 'zebra_crossing', I took it as meaning what's essentially animal crossing warning signs. Seeing 'pelican_crossing' as the only other result didn't help that mindset, but it did occur to me that zebras don't live in New Zealand, so some quick research explained the two (zebra crossings are the striped crosswalks and pelican crossings are pedestrian-controlled crossing lights). Now, though, after having that information, 39 total crossing references seems far too low so I'd like to look into that further as well.
```python
for row in cur.execute('SELECT value, count(value) FROM nodes_tags WHERE key="crossing_ref"
                        GROUP BY value ORDER BY count(value) desc'):
    print(row)
```
Results:
```python
('zebra', 36)
('pelican', 3)
```

### Data Problems
#### Street Name Suffixes
The occurrence of invalid street suffixes, or those that are formatted outside a standard manner, is shockingly low in my dataset. The only ones returned were `Ave`, `Christchurch`, `Close`, `Crescent`, `Green`, `Maidstone`, `Parade`, `Quay`, `Runway`, `School`, `Terrace`, `Tuam`, and `Valley`. The code below has several precursors to working properly, all of which can be found in the project submission.
```python
def audit():
    for event, elem in ET.iterparse(myMap, events=('start',)):
        if elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_street_name(tag):
                    check_road_types(road_types, tag.attrib['v'])
    pprint.pprint(dict(road_types))
```
A couple of these groups, `Crescent` and `Terrace`, are clearly just oversights I and others never added to the `expected` list, which is the simplest type of fix in that nothing needs to be fixed (although adding the two to the expected list is in order)! 'Christchurch' shows up only twice and both are cases where the user added the street, neighborhood, and city where only the street should be entered.

#### Keys
Plenty of keys have a very low count; in looking up the ones only with a single occurrence, it's clear that there are a lot of inappropriate entries. Some examples are `app`, `1`, `2`, `n`, and `start_date`. I've got a fairly simple standardization suggestion I'd make for a lot of the problems actually, so I'll go more in-depth with that below the problems section.
```python
con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT DISTINCT key FROM nodes_tags'):
    print(row)
con.close()
```

#### House Numbers
Querying the distinct `value` associated with a `key` of 'housenumber' showed a pretty hefty level of error. With a lot of these categories, the preference is to spell things out (hence "Road" instead of "Rd") but New Zealand's address conventions specifically work in a different way when it comes to the numbers. The standard format is to place a flat/unit number before the actual building number, separated with a slash, so the 4th unit of 165 A Street would be formatted `4/165 A Street`. It would seem a considerable amount of users chose to enter this information as `Flat 1, 100` or `Unit 18, 197` or actually several other non-standard formats.

Some others definitely look like they have the possibility of error, such as `99/1` as it seems unlikely that there would be a 99th unit in a building whose address number is 1. As far as these goes, there doesn't actually seem to be a way to clean it programatically (you could with the 'flat' and 'unit' ones) as so many of them would require item-by-item verification.

#### Others
* `entrance` should have qualification values, such as 'front,' 'main,' or 'handicap' but frequently people enter a simple 'yes,' which seems far more suited to the `access` tag. 
* In a single record, `key` has no value. It's not just the word 'None' but actually just none at all. That doesn't seem like something the programming would allow.

### Improvement Ideas
I've got a few ideas here I think could substantically improve the quality of obtained data. I'll be explaining each of these with the help of some user IDs from my map's top ten contributors.
```python
con = s3.connect(DB)
cur = con.cursor()
for row in cur.execute('SELECT DISTINCT n.user FROM nodes n
                        JOIN ways w on n.user = w.user LIMIT 10'):
    print(row)
con.close()
```

#### Blind Verification
For particularly problematic patterns, like if Tucson has a lot of quality issues overall or like in my case with the address number formatting, there could be a type of blind verification system. For a specific node, suppose the following values entered by users for a `key` of 'housenumber':
```
BCNorwich:  '5/164'
andrew_dc:  'Flat 5, 164'
EliotB:     '5-164'
kylenz:     '5/164'
brevans:    '5/164'
```
3 is an arbitrary amount chosen for demonstration purposes, but in this case, the data wouldn't actually be published until brevans entered the 3rd instance of an identical value. Now this could be frustrating for users who don't see their data being published initially and it would also take more time overall, but offers a definite quality check layer. In limiting the implementation of this, obviously fewer people would be affected by it.

The reason 'blind' is so important here is to avoid leading questions ('Is 5/164 correct?') as well as stop people from confirming by just clicking a 'Yes' button without paying attention.

#### Forced Standardization
Standardization would also only be used for certain fields and is definitely simple enough.
```
Misa_zumba enters '5 164' into the address number field but it's rejected
NZCoyote enters '5/164' and it's accepted because it's in one of the accepted formats for the area
```
This whole system could be made far easier by basing accepted formats on high-quality existing data. One problem with that is: would the incorrect address formats being used so heavily wind up accepted just because they're prevalent? There would also have to be systems in place to request adding additional formats. Overall there are probably a lot of roadblocks to implementing this idea but it could be extremely beneficial if feasible.

#### Automatic/Flagged Quality Check Requests
With a system to flag potential anomolies in the data (automatically comparing data as well as the ability for users to flag), items with a specific number or ratio of flags could be sent to users with high contribution rates and low flag rates.
```
lcmortensen notices a single anomolic zip code in their home town and flags it
koyel flags the same zip code and flags it
The system sends an auto-generated alert or email to Rudy355, a high-quality contributor from the area
Rudy can choose to accept the request to validate or refute the data
```
Users of a certain grade would be invited to opt-in to this system, on their terms. They could choose to receive requests as they come or in bulk at specific time intervals. Another option would be entirely at-will, like the user logs in to review any requests. This way, users wouldn't be receiving emails or alerts they don't want.
