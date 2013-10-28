Processing Steps
================

Pre-Steps
---------

1) make sure there are fields on the source location file for the input types; gid_closest, address, block, cai, mm, road

2) make sure there are is a field for transtech on each of the 'measure to' tables (address, block, cai, mm, road)

3) make sure all software dependencies are accounted for (postgis, pyscopg2, python

4) make sure all source and measure to datasets are in the right schema and projections, using these resources;
    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_shp.py
    - https://github.com/FCC/NBM-Processing/blob/master/Phase4/import/nbm_import_individual.py


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
- run the erate_road_fiber_ov.py script (yet to be developed)


Step 4 - run the erate_opt_ring.py script (yet to be developed).  
------
this script optimizes the distance to fiber for each school in a school district
