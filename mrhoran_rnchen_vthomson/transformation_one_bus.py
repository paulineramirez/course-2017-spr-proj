# part 1:minimum number of
# bus trips would be needed for each school 
# get # student per school
#  {student, schoool, their_address(coordinates)


# part 2:
#

#from which yard those
#buses should come
# get the # bus yards and their coordinates

import json
import dml
import prov.model
import datetime
import uuid
import ast
import sodapy
import time 

# this transformation will check how many comm gardens and food pantries there are for each area
# we want to take (zipcode, #comm gardens) (zipcode, #food pantries) --> (area, #food pantries#comm gardens)

class transformation_one(dml.Algorithm):

    contributor = 'mrhoran_rnchen'

    reads = ['mrhoran_rnchen_vthomson.student',
             'mrhoran_rnchen_vthomson.buses']

    writes = ['mrhoran_rnchen_vthomson.student_per_school',
              'mrhoran_rnchen_vthomson.buses_per_yard']

    @staticmethod
    def execute(trial = False):
        
        startTime = datetime.datetime.now()

        client = dml.pymongo.MongoClient()

        repo = client.repo
        
        repo.authenticate('mrhoran_rnchen_vthomson', 'mrhoran_rnchen_vthomson')
        
        X = project([x for x in repo.mrhoran_rnchen_vthomson.student.find({})], get_students)

        #A = project(X, lambda t: (t[3], (t[5], t[1])), 1)

        agg_student = aggregate(X, sum)
        
        #commgarden_zip_count = (project(aggregate(X, sum), lambda t: (t[0], ('comm_gardens',t[1]))))
                
        repo.dropCollection('student_per_school')
        repo.createCollection('student_per_school')

        #print(commgarden_zip_count)

        repo.mrhoran_rnchen_vthomson.student_per_school.insert(dict(agg_student))

############################
        
        Y = project([p for p in repo.mrhoran_rnchen_vthomson.buses.find({})], get_buses)

        bus_per_yard_count = aggregate(Y,sum)

           
        repo.dropCollection('buses_per_yard')
        repo.createCollection('buses_per_yard')
        
        repo.mrhoran_rnchen_vthomson.buses_per_yard.insert(dict(bus_per_yard_count))
       
##        # combine them to make a new data set like (zip, (comm,1), (foodp, 1))
##
##        temp = product(commgarden_zip_count, foodpantry_zip_count)
##
##        result = project(select(temp, lambda t: t[0][0] == t[1][0]), lambda t: (t[0][0], t[0][1], t[1][1]))
##
##        for z in commgarden_zip_count:
##            if z[0] not in result:
##                 result.append((z[0],z[1],('food_pantry',0)))
##
##        for p in foodpantry_zip_count:
##            if p[0] not in result:
##                 result.append((p[0],('comm_gardens',0),p[1]))
##
##        #print(result)
##
##        Y = project(result, lambda t: (t[0], (t[1], t[2])))
##
##        repo.dropCollection('garden_pantry_agg')
##        repo.createCollection('garden_pantry_agg')
##
##        repo.mrhoran_rnchen.garden_pantry_agg.insert(dict(Y))
       
        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}

    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('mrhoran_rnchen_vthomson', 'mrhoran_rnchen_vthomson')
        
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        #doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('dat:mrhoran_rnchen_vthomson#transformation_one', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})

        resource1 = doc.entity('dat:_bps_transportation_challenge/buses.json', {'prov:label':'Bus Yard Aggregation', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})

        get_buses_per_yard = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)

        doc.wasAssociatedWith(get_buses, this_script)

        doc.usage(get_buses, resource1, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  #'ont:Query':'location, area, coordinates, zip_code' #?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                  }
                  )

           # label section might be wrong
        resource2 = doc.entity('dat:_bps_transportation_challenge/schools.json', {'prov:label':'Student Aggregation', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})

        get_student_per_school = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)

        doc.wasAssociatedWith(get_students, this_script)

        doc.usage(get_students, resource1, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  #'ont:Query':'location, area, coordinates, zip_code' #?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                  }
                  )
        student_per_school = doc.entity('dat:mrhoran_rnchen_vthomson#student_per_school', {prov.model.PROV_LABEL:'Students per school', prov.model.PROV_TYPE:'ont:DataSet','ont:Extension':'json'})
        doc.wasAttributedTo(student_per_school, this_script)
        doc.wasGeneratedBy(student_per_school, get_students, endTime)
        doc.wasDerivedFrom(student_per_school, resource2, get_student_per_school, get_student_per_school, get_student_per_school)

    
        buses_per_yard = doc.entity('dat:mrhoran_rnchen_vthomson#buses_per_yard', {prov.model.PROV_LABEL:'Buses per yard', prov.model.PROV_TYPE:'ont:DataSet','ont:Extension':'json'})
        doc.wasAttributedTo(buses_per_yard, this_script)
        doc.wasGeneratedBy(buses_per_yard, get_buses_per_yard, endTime)
        doc.wasDerivedFrom(buses_per_yard, resource1, get_buses_per_yard, get_buses_per_yard, get_buses_per_yard)    
        repo.logout()
                  
        return doc


def aggregate(R, f):
    keys = {r[0] for r in R}
    return [(key, f([v for (k,v) in R if k == key])) for key in keys]
    
def select(R, s):
    return [t for t in R if s(t)]

def project(R, p):
    return [p(t) for t in R]

def product(R, S):
    return [(t,u) for t in R for u in S]


def get_students(student): # want to return the coordinates of the towns in and around Boston

    lat = student['School Latitude']
    long = student['School Longitude']
    name = student['Assigned School']

    return((name, (lat,long)), 1)

def get_buses(bus): # want to return the coordinates of the towns in and around Boston

    lat = bus['Bus Yard Latitude']
    long = bus['Bus Yard Longitude']
    name =  bus['Bus Yard']

    return((name, (lat,long)), 1)

transformation_one.execute()
doc = transformation_one.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof
