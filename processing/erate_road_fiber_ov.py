## ---------------------------------------------------------------------------
###   VERSION 0.1 (for postgis)
### erate_road_fiber_ov.py
### Created on: June 2, 20123
### Created by: Michael Byrne
### Federal Communications Commission 
##
## ---------------------------------------------------------------------------
##this script runs the analysis for distance to fiber for the road class in nbm
##the intent of this script is find the schools
##    - closest to other schools in the district
##    - and closest to a fiber source (road)

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
##road - the linear distance to fiber from the road feature in meters
##requires individual road tables by state to run

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
theTBL = "nces"

#function for finding the closest fiber in any feature class
def calc_rd_ov_100(myST):
  thepSQL = "psql -p 54321 -h " + myHost + " " + db + " -c "
	thepSQL = thepSQL + "'UPDATE " + schema + "." + theTBL + " set road = 0 "
	thepSQL = thepSQL + " FROM " + schema + "." + myST.lower() + "_road " 
	thepSQL = thepSQL + " WHERE ST_CONTAINS(" + myST.lower() + "_road.geom, "
	thepSQL = thepSQL + theTBL + ".geom) and transtech = 50;'"
	os.system(thepSQL)

def calc_rd_ov_lt_100(myST):
	#set up the connection to the database
	myConn = "dbname=" + db + " host=" + myHost + " port=" + myPort + " user=" + myUser
	conn = psycopg2.connect(myConn)

	#loop through for each gid where road is null
	#adding logic for other classes already likely connected (eg those < 200 meters are
	#likely connected already, so we only need to find those at a higher connection distanct
	#in other words, don't process the ones already at fiber
	dCur = conn.cursor()
	theSQL = "SELECT gid from " + schema + "." + theTBL + " WHERE road is NULL and " 
#	theSQL = theSQL + " addres > 200 and block > 200 and cai > 200 and middlemile > 200 and "
	theSQL = theSQL + " mstate = '" + myST + "'; "  
	print theSQL
	dCur.execute(theSQL)

	#if the record count > 0 then get the distance to the closest fiber 
	#points for selecting the closest schools in that district
	print "     doing this number of records: " + str(dCur.rowcount)
	myData = dCur.fetchall()
	for r in myData:
		myGID = r[0]
		updCur = conn.cursor()
		theSQL = "SELECT " + theTBL 
		theSQL = theSQL + ".gid, ST_DISTANCE(ST_TRANSFORM(" + theTBL 
		theSQL = theSQL + ".geom,9102010), ST_TRANSFORM(" + myST.lower() + "_road.geom,9102010)) "
		theSQL = theSQL + " FROM " + schema + "." + theTBL + ", " + schema + "." 
		theSQL = theSQL + myST.lower() + "_road " + " WHERE " + theTBL + ".gid = "
		theSQL = theSQL + str(myGID) + " and transtech = '50'"
		theSQL = theSQL + "  ORDER by st_distance  limit 1;"
		updCur.execute(theSQL)

		#if the record count > 0 then get the distance to the closest fiber 
		#points for selecting the closest schools in that district
		if updCur.rowcount == 1:
			ur = updCur.fetchone()
			uGID = ur[0]
			uDist = ur[1]
			#update theTable with the distance
			upd_val("road", uDist, uGID)
		updCur.close()
	conn.close()

#function finding the closest record and calc'ing the closest_gid to that value
def upd_val(myField, myVal, myID):
	#set up the connection to the database
	thepSQL = "psql -p 54321 -h " + myHost + " " + db + " -c " 
	thepSQL = thepSQL + "'UPDATE " + schema + "." + theTBL + " set " + myField + " = " + str(myVal) 
	thepSQL = thepSQL + " where gid = " + str(myID) + ";'"                	
	os.system(thepSQL)
    
try:
	States = ["AK","AL","AR","AS","AZ","CA","CO","CT"]          #1
	States = States + ["DE","FL","GA","GU","HI","IA","ID"] #2  "DC",
	States = States + ["IL","IN","KS","KY","LA","MA","MD","ME"] #3 
	States = States + ["MI","MN","MO","MS","MT","NC","ND"] #4 "MP",
	States = States + ["NE","NH","NJ","NM","NV","NY","OH","OK"] #5
	States = States + ["OR","PA","PR","RI","SC","SD","TN","TX"] #6
	States = States + ["UT","VA","VI","WA","WI","WV","WY"] #7 "VT",
	for theST in States:
		print "    working on the State: " + theST
		#this function calcs the road distance = 0 for all those points inside the 
		#the road table w/ fiber
		calc_rd_ov_100(theST)
		#this function cycles through all rows w/ a null road distance
		#and measures the distance to them
		calc_rd_ov_lt_100(theST)
	now = time.localtime(time.time())
	print "local time:", time.asctime(now)
except:
	print "something bad bad happened"     
      
      
