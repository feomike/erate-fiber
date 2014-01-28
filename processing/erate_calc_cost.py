## ---------------------------------------------------------------------------
###   VERSION 0.1 (for postgis)
### erate_calc_cost.py
### Created on: Jan. 27, 20143
### Created by: Michael Byrne
### Federal Communications Commission 
##
## ---------------------------------------------------------------------------
##set up the total costs


##dependencies
##run after cost distance is run
##software
##runs in python
##postgres/gis (open geo suite)
##the psycopg library
##data

##the output table "theTBL' variable below, needs to have the following fields to 
##accept values
##total_e_ad - euclidean distance cost with all distribution lines
##total_e_af - euclidean distance cost with all feeder lines
##total_e_m - euclidean distance cost with mixed distribution and feeder lines
##total_m_ad - manhattan distance cost with all distribution lines
##total_m_af - manhattan distance cost with all feeder lines
##total_m_m - manhattan distance cost with mixed distribution and feeder lines

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
schema = "sbi2013june"
theTBL = "nces_optring"
idF = "gid"
plantTBL = "plantmix"
cost_adj_TBL = "zip_cost_adjustment"
f2m = 3.28084

#return basic variables about the individual school location; 
#state, density, optdist, mandist
def returnLocationValues(myGid):
	myCur = conn.cursor()
	mySQL = "SELECT lstate, lzip, density, optdist, mandist FROM "
	mySQL = mySQL + schema + "." + theTBL + " where " + idF + "=" + myGid
	mySQL = mySQL + "and optring is not null ; "
	myCur.execute(mySQL)
	#row count should be 1
	if myCur.rowcount == 1:
		row = myCur.fetchone()
	else:
		row = ["None"]
	myCur.close()	
	return (row)

#return Cost Calculation Values for that state and density location
def returnCalcValues(myST, myDen):
	myCur = conn.cursor()
	mySQL = "SELECT aerial_ad/100, buried_ad/100, underground_ad/100, "
	mySQL = mySQL + "aerial_af/100, buried_af/100, underground_af/100, "
	mySQL = mySQL + "aerial_m/100, buried_m/100, underground_m/100 FROM " + schema + "."
	mySQL = mySQL + plantTBL + " WHERE state = '" + myST + "' and density = '"
	mySQL = mySQL + myDen + "'; "
	myCur.execute(mySQL)
	#row count should be 1
	if myCur.rowcount == 1:
		row = myCur.fetchone()
	else:
		row = ["None"]
	myCur.close()	
	return (row)

#return the Cost Adjustment value for the top 3 digits of the ZIP code
def returnCostAdjustment(myZIP):
	myVal = myZIP[:3]
	myCur = conn.cursor()
	mySQL = "SELECT adjrate FROM " + schema + "." + cost_adj_TBL
	mySQL = mySQL + " WHERE zip3 = '" + myVal + "' ; "
	myCur.execute(mySQL)
	#row count should be 1
	if myCur.rowcount ==1:
		row = myCur.fetchone()
	else:
		row = [1]
	myCur.close()	
	return(row[0])

#update the total cost vales on theTBL
def mkTotal(loc, calc, myCa, myGid):
	#format of loc is [0]=St; [1]=ZIP; [2]=density; [3]=euclidean; [4]=manhattan
	#format of calc is 	[0]=aerial_ad; [1]=buried_ad; [2]=underground_ad
	#					[3]=aerial_af; [4]=buried_af; [5]=underground_af
	#					[6]=aerial_mixed; [7]=buried_mixed; [8]=undergroun_mixed
	#	ad=all distribution option
	#	af=all feeder option
	#	mixed=average distribution and feeder option
	#
	a = 7.2
	if loc[2] == 'rural':
		b=5.36
		u=24.31
	if loc[2] == 'suburban':
		b=8.9
		u=28.37
	if loc[2] == 'urban':
		b=10.84
		u=33.37
	tot_e_ad = (a*float(loc[3])*float(calc[0])*f2m + b*float(loc[3])*float(calc[1])*f2m + u*float(loc[3])*float(calc[2])*f2m)*myCa
	tot_e_af = (a*float(loc[3])*float(calc[3])*f2m + b*float(loc[3])*float(calc[4])*f2m + u*float(loc[3])*float(calc[5])*f2m)*myCa
	tot_e_m =  (a*float(loc[3])*float(calc[6])*f2m + b*float(loc[3])*float(calc[7])*f2m + u*float(loc[3])*float(calc[8])*f2m)*myCa
	tot_m_ad = (a*float(loc[4])*float(calc[0])*f2m + b*float(loc[4])*float(calc[1])*f2m + u*float(loc[4])*float(calc[2])*f2m)*myCa
	tot_m_af = (a*float(loc[4])*float(calc[3])*f2m + b*float(loc[4])*float(calc[4])*f2m + u*float(loc[4])*float(calc[5])*f2m)*myCa
	tot_m_m =  (a*float(loc[4])*float(calc[6])*f2m + b*float(loc[4])*float(calc[7])*f2m + u*float(loc[4])*float(calc[8])*f2m)*myCa
	update_row(myGid, "total_e_ad", tot_e_ad)
	update_row(myGid, "total_e_af", tot_e_af)
	update_row(myGid, "total_e_m", tot_e_m)
	update_row(myGid, "total_m_ad", tot_m_ad)
	update_row(myGid, "total_m_af", tot_m_af)
	update_row(myGid, "total_m_m", tot_m_m)
	return

#function which updates the optdistance and optid
def update_row(myGID, myField, myVal):
	uCur = conn.cursor()
	uSQL = "UPDATE " + schema + "." + theTBL + " set " + myField + " = " + str(myVal)
	uSQL = uSQL + " where " + idF + " = " + str(myGID) + ";"
#	print uSQL
	uCur.execute(uSQL)                	              	
	conn.commit()	
	uCur.close()	

try:
	#set up the connection to the database
	myConn = "dbname=" + db + " host=" + myHost + " port=" + myPort + " user=" + myUser
	conn = psycopg2.connect(myConn)
	theCur = conn.cursor()
	#driver is one row at a time; uses a unique ID field
	theSQL = "SELECT MAX(" + idF + " ) from " + schema + "." + theTBL + "; "
	theCur.execute(theSQL)
	rows = theCur.fetchone()
	theCur.close()
	del theCur
	maxR = rows[0]
	r = 1
	print "going to operate on this many school: " + str(maxR)
	while r < maxR:
		Vals = []
		#get basic variables for this record; eg state, density, optdist, mandist
		locV = returnLocationValues(str(r))
		if locV[0] <> "None":
			#get calc variables
			calcV = returnCalcValues(locV[0], locV[2])
			#print calcV
			#get the cost adjustment
			ca = float(returnCostAdjustment(locV[1]))
			#update totals
			mkTotal(locV, calcV, ca, r)
		r = r + 1
	del conn, myConn
	now = time.localtime(time.time())
	print "local time:", time.asctime(now)
except:
	print "something bad bad happened"     
