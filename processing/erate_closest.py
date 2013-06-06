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
theTBL = "rockville"


#function finding the closest record and calc'ing the closest_gid to that value
def closest_gid(myGID):
  theCur = conn.cursor()
	theSQL = "SELECT leanm, ST_X(geom), ST_Y(geom) from " + schema + "." + theTBL
	theSQL = theSQL + " WHERE gid = " + str(myGID) + ";"
	theCur.execute(theSQL)
	
	#if the record count > 0 then get the leanm (school district) and x and y 
	#points for selecting the closest schools in that district
	if theCur.rowcount == 1:
		r = theCur.fetchone()
		theDist = r[0]
		theX = r[1]
		theY = r[2]
		#open a cursor to get the closest point
		#alter the sql if you want an additional and for the District
		theSQL = "SELECT gid FROM " + schema + "." + theTBL + " where gid <> " 
		theSQL = theSQL + str(myGID) + " ORDER BY geom <-> st_setsrid(st_makepoint(" 
		theSQL = theSQL + str(theX) + "," + str(theY) + "),4326) LIMIT 1;"
		idCur = conn.cursor()
		idCur.execute(theSQL)
		cGID = idCur.fetchone()[0]
		idCur.close()
		#update the current row to associate the new gid as the closest one
		upd_val("gid_closest", cGID, myGID)
	theCur.close()
     

#function finding the closest record and calc'ing the closest_gid to that value
def upd_val(myField, myVal, myID):
	uCur = conn.cursor()
	theSQL = "UPDATE " + schema + "." + theTBL + " set " + myField + " = " + str(myVal) 
	theSQL = theSQL + " where gid = " + str(myID)
	uCur.execute(theSQL)                	
	conn.commit()
	uCur.close()

#function for finding the closest fiber in any feature class
def closest_sbi(myType, myGID):
	dCur = conn.cursor()
	theSQL = "SELECT shp_" + myType + ".gid, ST_DISTANCE(ST_TRANSFORM(" + theTBL 
	theSQL = theSQL + ".geom,9102010), ST_TRANSFORM(shp_" + myType + ".geom,9102010)) "
	theSQL = theSQL + " FROM " + schema + "." + theTBL + ", " + schema + ".shp_" + myType
	theSQL = theSQL + " WHERE " + theTBL + ".gid = " + str(myGID) + " and transtech = '50'"
	theSQL = theSQL + "  ORDER by st_distance  limit 1;"
	dCur.execute(theSQL)
	#if the record count > 0 then get the distance to the closest fiber 
	#points for selecting the closest schools in that district
	if dCur.rowcount == 1:
		r = dCur.fetchone()
		theGID = r[0]
		theDist = r[1]
		#update theTable with the distance
		upd_val(myType, theDist, myGID)
	dCur.close()
    
try:
	#set up the connection to the database
	myConn = "dbname=" + db + " host=" + myHost + " port=" + myPort + " user=" + myUser
	conn = psycopg2.connect(myConn)
	theCur = conn.cursor()
	#get the total number of records to go through
	theSQL = "SELECT count(*) from " + schema + "." + theTBL + ";"
	theCur.execute(theSQL)
	theID = theCur.fetchone()[0]
	theCur.close()
	del theCur
	print "going to be operating on this many locations: " + str(theID)
	i = 0
	while i < theID:
		print "    begining work on row: " + str(i)
		i = i + 1
		closest_gid(i)
		for myType in ["address"]:  #, "road", "block", "cai", "middlemile"
			closest_sbi(myType, i)

except:
	print "something bad bad happened"     
      
      
