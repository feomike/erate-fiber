## ---------------------------------------------------------------------------
###   VERSION 0.1 (for postgis)
### erate_draw_ring.py
### Created on: June 2, 20123
### Created by: Michael Byrne
### Federal Communications Commission 
##
## ---------------------------------------------------------------------------
##this script creates the geometry of the new rings created by the erate_opt_ring.py script
##the intent of this script is find the schools


##dependencies
##software
##runs in python
##postgres/gis (open geo suite)
##the psycopg library
##data

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
theOTBL = "aatest"

def create_feature_rows(myGID):
  	sCur = conn.cursor() #for getting all the attributes cursor
	theSQL = "SELECT gid, leaid, optgid, optdist, optring, st_x(geom), st_y(geom), " 
	theSQL = theSQL + " mandist FROM " + schema + "." + theTBL + " where gid = "  
	theSQL = theSQL + str(myGID) + ";"
	sCur.execute(theSQL)	
	r = sCur.fetchone()
	gid = r[0]
	leaid = r[1]
	optgid = r[2]
	myX = r[5]
	myY = r[6]	
	if str(r[0]) == str(r[2]): #the write the point
		theSQL = "INSERT INTO " + schema + "." + theOTBL 
		theSQL = theSQL + " (leaid, optgid, optdist, optring, mandist, geom) " 
		theSQL = theSQL + " values ( " 
		theSQL = theSQL + str(r[1]) + ", " + str(r[2]) + ", " + str(r[3]) + ", " 
		theSQL = theSQL + str(r[4]) + ", " + str(r[7]) + ", "
		theSQL = theSQL + "ST_PointFromText('POINT(" + str(r[5]) + " " + str(r[6]) + ")' "
		theSQL = theSQL + ", 4326)); "
		theSQL = theSQL + " commit; "
		sCur.execute(theSQL)
	else: #insert the point and the line
		#insert the points
		theSQL = "INSERT INTO " + schema + "." + theOTBL 
		theSQL = theSQL + " (leaid, optgid, optdist, optring, mandist, geom) " 
		theSQL = theSQL + " values ( " 
		theSQL = theSQL + str(r[1]) + ", " + str(r[2]) + ", " + str(r[3])
		theSQL = theSQL + ", " + str(r[4]) + ", " + str(r[7]) + ", "
		theSQL = theSQL + "ST_PointFromText('POINT(" + str(r[5]) + " " + str(r[6]) + ")' "
		theSQL = theSQL + ", 4326)); "
		theSQL = theSQL + " commit; "
		sCur.execute(theSQL)	
		theSQL = "select leaid, optgid, optdist, optring, st_x(geom), st_y(geom), "
		theSQL = theSQL + "mandist  FROM "
		theSQL = theSQL + schema + "." + theTBL + " where gid = " + str(optgid) + ";"
		sCur.execute(theSQL)
		r = sCur.fetchone()
		theSQL = "INSERT INTO " + schema + "." + theOTBL 
		theSQL = theSQL + " (leaid, optgid, optdist, optring, mandist, geom) " 
		theSQL = theSQL + " values ( " 
		theSQL = theSQL + str(r[0]) + ", " + str(r[1]) + ", " + str(r[2])
		theSQL = theSQL + ", " + str(r[3]) + ", " + str(r[6]) + ", "
		theSQL = theSQL + "ST_GeomFromText('LINESTRING(" + str(myX) + " " + str(myY) + ", " 
		theSQL = theSQL + str(r[4]) + " " + str(r[5]) + ")', 4326) ); commit;"
		sCur.execute(theSQL)		
	sCur.close()
				
try:
	#set up the connection to the database
	myConn = "dbname=" + db + " host=" + myHost + " port=" + myPort + " user=" + myUser
	conn = psycopg2.connect(myConn)
	theCur = conn.cursor()
	#delete theOTBL if it exists
	theSQL = "drop table if exists " + schema + "." + theOTBL + "; "
	theSQL = theSQL + "CREATE TABLE " + schema + "." + theOTBL + " AS SELECT "
	theSQL = theSQL + "leaid, optgid, optdist, optring, mandist, geom FROM " 
	theSQL = theSQL + schema + "." + theTBL + " limit 1; "
	theSQL = theSQL + "TRUNCATE " + schema + "." + theOTBL + "; "
	theSQL = theSQL + "ALTER TABLE " + schema + "." + theOTBL + " add column gid serial; commit; "
	theSQL = theSQL + "alter table " + schema + "." + theOTBL 
	theSQL = theSQL + " add CONSTRAINT " + schema + "_" + theOTBL + "_pkey_gid PRIMARY KEY (gid),"
	theSQL = theSQL + " add CONSTRAINT enforce_dims_geom CHECK (st_ndims(geom) = 2), "
	theSQL = theSQL + " add CONSTRAINT enforce_srid_geom CHECK (st_srid(geom) = 4326); "
	theSQL = theSQL + " CREATE INDEX " + schema + "_" + theOTBL + "_geom_gist "
	theSQL = theSQL + " ON " + schema + "." + theOTBL + " USING gist (geom); "
	theSQL = theSQL + " commit;"
	theCur.execute(theSQL)		
	#get the total number of records to go through
	theSQL = "SELECT gid from " + schema + "." + theTBL + ";" 
	theCur.execute(theSQL)
	driver = theCur.fetchall()
	print "going to operate on this many records: " + str(theCur.rowcount)
	for r in driver:
		theGID = r[0]
		print "  working on gid: " + str(theGID)
		#run draw features
		create_feature_rows(theGID)
	theCur.close()
	del theCur
	del conn, myConn
	now = time.localtime(time.time())
	print "local time:", time.asctime(now)
except:
	print "something bad bad happened"     
