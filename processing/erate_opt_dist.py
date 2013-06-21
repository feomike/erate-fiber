## ---------------------------------------------------------------------------
###   VERSION 0.1 (for postgis)
### erate_closest.py
### Created on: June 2, 20123
### Created by: Michael Byrne
### Federal Communications Commission 
##
## ---------------------------------------------------------------------------
##this script runs the setup for the erate analysis
##the intent of this script is find the schools
##    - closest to other schools in the district
##    - and closest to a fiber source
##this script forms the distance as a the optimal ring structure, 
##beginning w/ the distance to the
##shortest fiber; it does  optimize for the shortest distance because it does find
##the next ring path distance as the shorter of the two between the 
##least(addres, block, cai, middlemile, road) distance and the next closest fiber

##dependencies
##software
##runs in python
##postgres/gis (open geo suite)
##the psycopg library
##data
##a shapefile of the the buffers of the towers excluding lpfm
##creates 1 output shapefile per channel
##uses epsg 102010 - http://spatialreference.org/ref/esri/102010/
##the output table "theTble' variable below, needs to have the following fields to 
##accept values
##gid_closest (becomes the ID of the next closest feature in theTble
##address - the linear distance to fiber from the address feature in meters
##block - the linear distance to fiber from the block feature in meters
##road - the linear distance to fiber from the road feature in meters
##cai - the linear distance to fiber from the cai features feature in meters
##middle mile - the linear distance to fiber from the middle mile feature in meters

# Import system modules
import sys, string, os
import psycopg2
import time
now = time.localtime(time.time())
print "local time:", time.asctime(now)

#variables
myHost = "localhost"
myPort = "54321"
myUser = "postgres"
db = "feomike"
schema = "sbi2012dec"
theTBL = "nces_flint1"
districtField = "leaid"

#find the next closest site 
def get_nextclosest_gid(myDist):
  #this function gets the closest feature (gid, and its least distance to fiber)
	#without fiber, to those with fiber (or already allocated)
	#the result is always only 1 feature
  	cCur = conn.cursor() #for closest cursor
	theSQL = "SELECT gid, least(addres, block, cai, middlemile, road), st_x(geom), st_y(geom) from "
	theSQL = theSQL + schema + "." + theTBL + " where st_intersects(" + theTBL + ".geom, "
	theSQL = theSQL + "( SELECT st_closestPoint ( "
	theSQL = theSQL + "( select st_union(geom) from " + schema
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDist + "' "
	theSQL = theSQL + " and optring is null group by " + districtField + ") , "
	theSQL = theSQL + " ( select st_union(geom) from " + schema
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDist + "' "
	theSQL = theSQL + " and optring is not null group by " + districtField + ") ) "
	theSQL = theSQL + " ) ) and optring is null;"
  	cCur.execute(theSQL)	
  	r = cCur.fetchone()	
  	cCur.close()
  	return r

#function finding the closest record and calc'ing the closest_gid to that value
#myGID is the next closest w/o fiber, theDistrict, theLeast, myX, myY
def closest_fiber_gid(myGID, myDist, myLength, optRing, myX, myY):
	#find closet GID and distance to that GID from this myGID where it does have fiber
	theSQL = "SELECT gid, ST_DISTANCE(st_transform(geom,9102010), st_transform("
	theSQL = theSQL + "ST_GeomFromText('POINT(" + myX + " " + myY + ")',4326), 9102010))"
	theSQL = theSQL + " FROM " + schema + "." + theTBL + " where gid <> " + str(myGID)
	theSQL = theSQL + " and " + districtField + " = '" + myDist + "' "
	theSQL = theSQL + " and optdist > -1 "
	theSQL = theSQL + " ORDER BY geom <-> st_setsrid(st_makepoint(" 
	theSQL = theSQL + str(myX) + "," + str(myY) + "),4326) LIMIT 1;"
	optCur = conn.cursor()
	optCur.execute(theSQL)
	r = optCur.fetchone()
	#check to see if there are any features which have a lower distance to
	#fiber (e.g. least(...)) than the distance to the next one (e.g. cDist)
	theSQL = "select gid, least(addres, block, cai, middlemile, road) as len from "
	theSQL = theSQL + schema + "." + theTBL + " where least(addres, block, cai, "
	theSQL = theSQL + "middlemile, road) < " + str(r[1]) + " and optring is null and "
	theSQL = theSQL + districtField + " = '" + myDist + "' order by len limit 1;"
	optCur.execute(theSQL)
	#if there is at least one row, then there is a closer fiber endpoint than the next
	#closest school
	if optCur.rowcount == 1:
		optr = optCur.fetchone()
		cGID = str(optr[0])
		theLeast = str(int(optr[1]))
		theGID = str(cGID)
	else:  #use the closest school
		theLeast = int(r[1])
		theGID = myGID
		cGID = r[0]
	optCur.close()
	del optCur
	upd_val("optdist", theLeast, theGID)
	upd_val("optgid", cGID, theGID)
	upd_val("optring", optRing, theGID)

 
#function finding the closest record and calc'ing the closest_gid to that value
def upd_val(myField, myVal, myID):
	uCur = conn.cursor()
	theSQL = "UPDATE " + schema + "." + theTBL + " set " + myField + " = " + str(myVal) 
	theSQL = theSQL + " where gid = " + str(myID)
	uCur.execute(theSQL)                	
	conn.commit()
	uCur.close()


#set the starting point for the connection in a district
#the starting point in the district is the single school with the lowest
#distance to an external fiber connection
#an external fiber connection, is previously calculated and is stored as a distance 
#from that school to a fiber endpoint.  the fields are addres, block, cai, mm, and road
#the distance in that field is meters from the school to the closest fiber
def calc_start(myDistrict):
	dCur = conn.cursor()  #district cursor
	#get all records in a district
	theSQL = "SELECT gid, least(addres, block, cai, middlemile, road) from "  + schema
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDistrict  
	theSQL = theSQL + "' order by least(addres, block, cai, middlemile, road) limit 1;"
	dCur.execute(theSQL)
	if dCur.rowcount == 1:  
		r = dCur.fetchone()
		#upd_val(myField, myVal, myID - the field to calc, the value to calc, at the ID
		#once the fields, optdist, optgid, and optring have non-null values, we assume
		#that that school is now connected to fiber
		upd_val("optdist", r[1], r[0])
		upd_val("optgid", r[0], r[0])
		upd_val("optring", 0, r[0])


#function which updates trigger fields (optdist, optgid, and optring) if that school
#has fiber because it has a least 0 distance or least distance less than 200 meters
#from the school to a fiber location.  
#once the trigger fields are updated to a value, from a null, it is considered ready to 
#be an spoke for other schools to be connected
def calc_opt_length_with_fiber(myDistrict):
	dCur = conn.cursor()  #district cursor
	#get all records in a district
	theSQL = "SELECT gid, least(addres, block, cai, middlemile, road) from "  + schema 
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDistrict + "';"
	dCur.execute(theSQL)
	if dCur.rowcount == 1:  #there is only one school in the district
		r = dCur.fetchone()
		#upd_val(myField, myVal, myID - the field to calc, the value to calc, at the ID
		upd_val("optdist", r[1], r[0])
		upd_val("optgid", r[0], r[0])
		upd_val("optring", 0, r[0])
	else:  #if there are many schools in the district
		rows = dCur.fetchall()
		#if the distance is < 200, it has access to fiber
		for r in rows:
			if r[1] < 200:  #then the school has fiber because of proximity
				upd_val("optdist", r[1], r[0])
				upd_val("optgid", r[0], r[0])
				#an optring of -1 means it is with 200 meters
				upd_val("optring", -1, r[0])
			
#function which finds the optimal distance for those w/o fiber
def calc_opt_length_wo_fiber(myDistrict):
	#find the number of rows w/o fiber in the district, and put it in a counting variable
	#set up a loop to repeat until you have no schools left to allocate
	dCur = conn.cursor()  #district cursor
	#get all records in a district who don't already have fiber
	theSQL = "SELECT gid  from " + schema + "." + theTBL + " where " + districtField
	theSQL = theSQL  + " = '" + myDistrict + "' and optdist is NULL;"
	dCur.execute(theSQL)
	theCnt = dCur.rowcount
	myCnt = 1
	dCur.close()
	#while there are schools left in the district to optimize
	while myCnt <= theCnt:
		#find next closest school w/o fiber and its least distance to a fiber location
		#return the gid, and the least distance
		r = get_nextclosest_gid(myDistrict)
		print "    doing myCnt: " + str(myCnt)
		#passing in gid for the next closest w/o fiber, theDistrict, theLeast, X, and Y
		closest_fiber_gid(r[0], myDistrict, r[1], myCnt, str(r[2]), str(r[3]))
		myCnt = myCnt + 1

#function which updates the optdistance and optid
def update_row(myGID, optDist, optGID):
	uCur = conn.cursor()
	uSQL = "UPDATE " + schema + "." + theTBL + " set optdist = " + str(optDist)
	uSQL = uSQL + " where gid = " + str(myGID) + ";"
	uCur.execute(uSQL)                	
	conn.commit()
	uSQL = "UPDATE " + schema + "." + theTBL + " set optgid = " + str(optGID) 
	uSQL = uSQL + " where gid = " + str(myGID) + ";"
	uCur.execute(uSQL)                	
	conn.commit()	
	uCur.close()	

try:
	#set up the connection to the database
	myConn = "dbname=" + db + " host=" + myHost + " port=" + myPort + " user=" + myUser
	conn = psycopg2.connect(myConn)
	theCur = conn.cursor()
	#get the total number of records to go through
	theSQL = "SELECT " + districtField + ", count(*) from " + schema + "." + theTBL
	theSQL = theSQL + " group by " + districtField + " order by count; "
	theCur.execute(theSQL)
	driver = theCur.fetchall()
	print "going to operate on this many school districts: " + str(theCur.rowcount)
	for r in driver:
		theDistrict = str(r[0])
		print "  working on district: " + theDistrict
		#run optimal
		calc_start(theDistrict)		
		calc_opt_length_with_fiber(theDistrict)
		calc_opt_length_wo_fiber(theDistrict)
	theCur.close()
	del theCur
	del conn, myConn
	now = time.localtime(time.time())
	print "local time:", time.asctime(now)
except:
	print "something bad bad happened"     
