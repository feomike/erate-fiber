Processing Steps
================
The goal of this effort is to establish a comprehensive distance from fiber for each k-12 school in the United States.  These processing steps establish that distance.  Once a distance is established a separate effort uses those distances to calculate a potential cost of getting fiber to each school. 

This process has two main halfs;  in part one we **establish** the physical distance from each school, to the school's **closest fiber location**.  this processing is one school at a time, against sources of fiber locations from the national broadband map.  sources of fiber locations has two processing steps.  in step one, we use fiber location from addresses, community anchor institutions, and middle mile locations in the national broadband amp.  for these data sources, the process is optimized from single nationwide datasets (e.g. a nationwide community anchor institution table).  step two is processing block and road data from the national broadband map.  this process is optimized to run on state tables (e.g. block_ak ... block_wy). 

at the end of the first half, all schools have a euclidean (strait) distance to sources of fiber (address, block, cai, middlemile and cai) and also has the unique id (gid) of the closests school to that school.  

in part two of the analysis we eastablish the **optimum distance to link all schools in a district**.  part two runs one school district at a time; then within each district one school at a time.  the optimization routine selects all schools in a district, then establishes all of the schools with fiber (e.g. they are 0 meters or less than certain a distance from fiber which would allow us to assume they have fiber).  Next it takes the remaining schools and links them ordinally, based on the school that is closest to a fiber location, including the set of newly connected schools, and connects them one at a time. once a school is connected, it is used to help connect other schools within that district.

at the end of the second half process, all schools then have populated fields for, the connection order for connecting schools in a district (0 through n; a -1 means it already had fiber)
- the euclidean and manhatthan distance for connecting the schools within a district


The process operates on a table for NCES locations (aka source location file below).  the table, needs to have a geometry column built from the latitude and longitude fields. 

Pre-Steps
---------

1.a) make sure there are fields on the source location file (eg NCES table in postgres) for the input types; 
- gid_closest
- address
- block
- cai
- middlemile
- road

1.b) the school table will also need fields for; 
- optdist - the optimum euclidean distance to connect the school given the district schools distance to fiber and spatial distribution of schools
- optring - the ordinal connection level (smallest first)
- mandist - the manhattan distance to connect the school given the district schools distance to fiber and spatial distribution of schools

All of the above fields should be initialized to NUll when begining the processing steps.


2) make sure there are is a field for transtech on each of the 'measure to' tables (address, block, cai, mm, road);  each of the source broadband map tables need to have a field called transtech.  in this field a transtech code of 50 determines fiber.  for address, block, community anchor institutions, and road, this field and these codes are standard.  however, for middlemile, a transtech field needs to be added and calculated based on the current data model fields (bh_type) to determine fiber.

3) make sure all software dependencies are accounted for (postgis, pyscopg2, python).

4) make sure all datasets are in the right schema and projections.  The tables need to be all in wgs84 projection and in one schema;
- schools - a table of points representing schools.  it needs an attribute for unique ID (eg gid) and for school district (from nces leaid)
- address - a single nationwide layer of addresses representing availability from NBM from addresses.  needs a field called transtech populate w/ standard ntia/fcc codes for technology of transmission
- block - 56 polygon tables of block level availability w/ a field call transtech (same as address).  the naming convention needs to be <state>_block
- cai - a single nationwide point layer of community anchor institutions w/ broadband availability and a transtech field
- middle mile - a single nationwide point layer of middle mile locations w/ a transtech field
- road - 56 polygon tables of availability along roads w/ transtech field.  the naming convention needs to be <state>_road.

use the below links to help import shapefiles from the NBM download site to an appropriate schema/table structure

    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_shp.py (address, community anchor insitution and middle mile)
    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_individual.py (block and road)


##Processing Steps


Step 1 - get distance to closest address, cai, mm
------
- run the erate-closest.py script.  this script works off of the national layers for address, cai and mm.


Step 2 - get distance to closest block
------
- run the erate_block_fiber_ov.py script.  this script works on state block tables, rather than a nationwide layer, b/c it is tons faster. this script has a stepwise approach
  - it takes all of those nces locations which are contained by fiber footprint, and assigns them a 0 distance
  - then it works on only the remaining nces locations and assigns them the distance to the closest fiber block footprint


Step 3 - get distance to closest road
------
- run the erate_road_fiber_ov.py script. this script works on state road tables, rather than a nationwide layer, b/c it is tons faster. this script has a stepwise approach
  - it takes all of those nces locations which are contained by fiber footprint, and assigns them a 0 distance
  - then it works on only the remaining nces locations and assigns them the distance to the closest fiber block footprint


Step 4 - run the erate_opt_ring.py script.  
------
this script optimizes the distance to fiber for each school in a school district
