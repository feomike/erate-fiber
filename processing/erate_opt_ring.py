## ---------------------------------------------------------------------------
###   VERSION 0.1 (for postgis)
### erate_opt_ring.py
### Created on: June 14, 20123
### Created by: Michael Byrne
### Federal Communications Commission 
##
## ---------------------------------------------------------------------------
##this script runs the optimization for the erate analysis
##the intent of this script is find the schools
##    - closest to other schools in the district
##    - and closest to a fiber source

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
theTBL = "nces_test"
districtField = "leaid"


#function finding the closest record and calc'ing the closest_gid to that value
def closest_gid(myGID, myDist, myLength):
  #get XY of the current GID
  	cCur = conn.cursor() #for closest cursor
	theSQL = "SELECT ST_X(geom), ST_Y(geom) from " + schema + "." + theTBL
	theSQL = theSQL + " WHERE gid = " + str(myGID) + ";"
	cCur.execute(theSQL)
	
	#if the record count > 0 then get the leanm (school district) and x and y 
	#points for selecting the closest schools in that district
	if cCur.rowcount == 1:
		r = cCur.fetchone()
		myX = str(r[0])
		myY = str(r[1])
		#find closet GID and distance to that GID from this GID
		theSQL = "SELECT gid, ST_DISTANCE(st_transform(geom,9102010), st_transform("
		theSQL = theSQL + "ST_GeomFromText('POINT(" + myX + " " + myY + ")',4326), 9102010))"
		theSQL = theSQL + " FROM " + schema + "." + theTBL + " where gid <> " + str(myGID)
		theSQL = theSQL + " and " + districtField + " = '" + myDist + "' "
		theSQL = theSQL + " ORDER BY geom <-> st_setsrid(st_makepoint(" 
		theSQL = theSQL + str(myX) + "," + str(myY) + "),4326) LIMIT 1;"
		optCur = conn.cursor()
		optCur.execute(theSQL)
		r = optCur.fetchone()
		cGID = r[0]
		cDist = r[1]
		optCur.close()
		del optCur
		#compare that distance to the least of the distance to fiber
		#use the shorter of the two distances

		if cDist < myLength:
			theLeast = cDist
		else:
			theLeast = myLength
		upd_val("optdist", theLeast, myGID)
		upd_val("optgid", cGID, myGID)
	cCur.close()
 

#function finding the closest record and calc'ing the closest_gid to that value
def upd_val(myField, myVal, myID):
	uCur = conn.cursor()
	theSQL = "UPDATE " + schema + "." + theTBL + " set " + myField + " = " + str(myVal) 
	theSQL = theSQL + " where gid = " + str(myID)
	uCur.execute(theSQL)                	
	conn.commit()
	uCur.close()

#function which finds the optimal distance, for those locations already w/ fiber
def calc_opt_length_with_fiber(myDistrict):
	dCur = conn.cursor()  #district cursor
	#get all records in a district
	theSQL = "SELECT gid, least(addres, block, cai, middlemile, road) from "  + schema 
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDistrict + "';"
	dCur.execute(theSQL)
	if dCur.rowcount == 1:  #there is only one school in the district
		r = dCur.fetchone()
		upd_val("optdist", r[1], r[0])
		upd_val("optgid", r[0], r[0])
	else:  #if there are many schools in the district
		rows = dCur.fetchall()
		#if the distance is < 200, it has access to fiber
		for r in rows:
			if r[1] < 200:  #then the school has fiber because of proximity
				upd_val("optdist", r[1], r[0])
				upd_val("optgid", r[0], r[0])
			
#function which finds the optimal distance for those w/o fiber
def calc_opt_length_wo_fiber(myDistrict):
	#find the number of rows w/o fiber in the district, and put it in a counting variable
	#set up a loop to repeat until you have no schools left to allocate
	dCur = conn.cursor()  #district cursor
	#get all records in a district
	theSQL = "SELECT gid, least(addres, block, cai, middlemile, road) from "  + schema 
	theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDistrict 
	theSQL = theSQL + "' and optdist is NULL;"
	dCur.execute(theSQL)
	theCnt = dCur.rowcount
	myCnt = 0

	#while there are schools left in the district to optimize
	while myCnt <> theCnt:
		#find next closest school w/ fiber and calculate the optdist and optid
		r = dCur.fetchone()
		#dCur.close()
		closest_gid(r[0], myDistrict, r[1])
		#re issue the counting varible
		theSQL = "SELECT gid, least(addres, block, cai, middlemile, road) from "  + schema 
		theSQL = theSQL + "." + theTBL + " where " + districtField + " = '" + myDistrict 
		theSQL = theSQL + "' and optdist is NULL;"
		dCur.execute(theSQL)
		theCnt = dCur.rowcount
#		print theCnt
		#theCnt = 0

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
		print "     working on district: " + theDistrict
		#run optimal		
		calc_opt_length_with_fiber(theDistrict)
		calc_opt_length_wo_fiber(theDistrict)
	theCur.close()
	del theCur
	del conn, myConn
	now = time.localtime(time.time())
	print "local time:", time.asctime(now)
except:
	print "something bad bad happened"     



#Optimal code
#For each district
#  Select schools in district order by least
#     If row count = 1
#        Opt dist = least dist
#        Optgid = least gid

#     If row count > 1
#        If least dist < 200
#             Update:
#          A      Opt dist = least dist
#                Optgid = gid
#while there are schools left to optimize
#        If least dist > 200
#            Find closest school in district with an optimal
#                 Update optimal w/ distance to that closest facility      
#      



#function for finding the closest fiber in any feature class
#def closest_sbi(myType, myGID):
#	dCur = conn.cursor()  #driver cursor
#	theSQL = "SELECT shp_" + myType + ".gid, ST_DISTANCE(ST_TRANSFORM(" + theTBL 
#	theSQL = theSQL + ".geom,9102010), ST_TRANSFORM(shp_" + myType + ".geom,9102010)) "
#	theSQL = theSQL + ", shp_" + myType + ".gid"
#	theSQL = theSQL + " FROM " + schema + "." + theTBL + ", " + schema + ".shp_" + myType
#	theSQL = theSQL + " WHERE " + theTBL + ".gid = " + str(myGID) + " and transtech = '50'"
#	theSQL = theSQL + "  ORDER by st_distance  limit 1;"
#	dCur.execute(theSQL)

#	#if the record count > 0 then get the distance to the closest fiber 
#	#points for selecting the closest schools in that district
#	if dCur.rowcount == 1:
#		r = dCur.fetchone()
#		theGID = r[0]
#		theDist = r[1]
#		theOtherGID = r[2]
#		#update theTable with the distance
#		upd_val(myType, theDist, myGID)
##		print "theOtherGID is: " + str(theOtherGID) + " and the dist is: " + str(theDist)
#	dCur.close()
