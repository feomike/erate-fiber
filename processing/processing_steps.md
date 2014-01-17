Processing Steps
================
This process has two main halfs;  in part one we establish the physical distance from each school, to its closest fiber location.  in part one the operation is one school at a time, against sources of fiber locations.  fiber locations is found in two parts as well.  in part one, we use fiber location from the national broadband map from addresses, community anchor institutions, and middle mile locations.  for these data sources, the process is optimized from single nationwide datasets of the fiber location (e.g. a nationwide community anchor institution table).  part two is block and road.  the process is optimized if run such that the input source tables are state tables (e.g. block_ak ... block_wy).   

in part two of the analysis we eastablish the optimum distance to link all schools in a district.  part two runs one school district at a time.  the optimization routine selects all schools in a district, then establishes all of the schools with fiber (e.g. they are 0 or less than a distance from fiber which would allow us to assume they have fiber), then repeats for all schools in that district finding the next closest school to connect.  once a school is connected, it is used to help connect other schools in the district.

at the end of the process, all schools then have populated attributes for:
- the euclidean (strait) distance from that school to each fiber source (address, block, cai, middle mile and road)
- the connection order for connecting schools in a district (-1 is a school already w/ fiber)
- the euclidean and manhatthan distance for connecting the schools within a district



Pre-Steps
---------

1) make sure there are fields on the source location file for the input types; 
- gid_closest
- address
- block
- cai
- middlemile
- road
1.a) the school table will also need fields for 
- optdist - the optimum euclidean distance to connect the school given the district schools distance to fiber and spatial distribution of schools
- optrint - the ordinal connection level (smallest first)
- mandist - the manhattan distance to connect the school given the district schools distance to fiber and spatial distribution of schools


2) make sure there are is a field for transtech on each of the 'measure to' tables (address, block, cai, mm, road);  each of the source broadband map tables need to have a field called transtech.  in this field a transtech code of 50 determines fiber.  for address, block, community anchor institutions, and road, this field and these codes are standard.  however, for middlemile, a transtech field needs to be added and calculated based on the current data model fields (bh_type) to determine fiber.

3) make sure all software dependencies are accounted for (postgis, pyscopg2, python).

4) make sure all source and measure to datasets are in the right schema and projections, using these resources;
    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_shp.py (address, community anchor insitution and middle mile)
    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_individual.py (block and road)


Step 1 - get distance to closest address, cai, mm
------
- run the erate-closest.py script.  this script works off of the national layers for address, cai and mm.


Step 2 - get distance to closest block
------
- run the erate_block_fiber_ov.py script.  this script works on state block shapes, rather than a nationwide layer, b/c it is tons faster. this script has a stepwise approach
  - it takes all of those nces locations which are contained by fiber footprint, and assigns them a 0 distance
  - then it works on only the remaining nces locations and assigns them the distance to the closest fiber block footprint


Step 3 - get distance to closest road
------
- run the erate_road_fiber_ov.py script 


Step 4 - run the erate_opt_ring.py script (yet to be developed).  
------
this script optimizes the distance to fiber for each school in a school district
