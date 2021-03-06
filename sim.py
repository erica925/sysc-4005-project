import random
import numpy as np
import math

#create counters to test for little's law
c1_in = 0
c2_in = 0
c3_in = 0
c1_out = 0
c2_out = 0
c3_out = 0

c1_list = []
c2_list = []
c3_list = []

c1_times = []
c2_times = []
c3_times = []

c1_samples = []
c2_samples = []
c3_samples = []

#creates a linear congruential generator to generate numbers between 0 and 1
class LinearCongruentialGenerator():
    def __init__(self, a, c, m, x0):
        self.a = a
        self.c = c
        self.m = m
        self.x = x0
    #returns a random number between 0 and 1
    def getRandomNumber(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m
    
#returns a random value from the exponential distribution defined by the given lambda parameter
#uses a randomly generated number from 0 to 1 and the inverse transform technique
def getExponential(lam):
    r = 0
    while r == 0:
        r = lin_con_gen.getRandomNumber()
    return -1 / lam * math.log(r)

#calculates the MLE estimator for the lambda parameter of an exponential distribution based on the given dataset
def lam_estimator(data):
    return len(data) / sum(data)

#defines an inspector entity
class Inspector():
    #creates the inspector
    def __init__(self, id):
        self.id = id
        self.waiting = False
        self.waitingSinceTime = None
        self.totalWaitTime = 0
    #returns all buffers attached to this inspector
    def getFreeBuffers(self, comp):
        list = []
        for b in BUFFERS:
            if b.component == comp and b.capacity < 2:
                list.append(b)
        return list
        
#defines a component entity
class Component():
    #creates the component
    def __init__(self, id):
        self.id = id  
        
#defines a buffer entity
class Buffer():
    #creates the buffer with an attached inspector, component type, and workstation
    def __init__(self, workstation, inspector, component):
        self.workstation = workstation
        self.inspector = inspector
        self.component = component
        self.capacity = 0
        self.timeOfLastCapacityChange = 0
        self.totalCapacityMinutes = 0
        
#defines a workstation entity
class Workstation():
    #creates the workstation
    def __init__(self, id):
        self.id = id  
        self.busy = False
        self.totalBusyTime = 0
        self.productsCompleted = 0
    #checks if the buffers attached to this workstation contain enough components to assemble a product
    def hasComponentsReady(self):
        for b in self.getBuffers():
            if b.capacity == 0:
                return False
        return True
    #returns all buffers attached to this workstation
    def getBuffers(self):
        list = []
        for b in BUFFERS:
            if b.workstation == self:
                list.append(b)
        return list

#defines an event type for when an inspector puts a component in a buffer
class BufferFillEvent():
    #creates the event
    def __init__(self, time, buffer):
        self.buffer = buffer 
        self.time = time
    #returns a description of the event
    def desc(self):
        return "BFE | t: " + str(self.time) + " | I: " + str(self.buffer.inspector.id) + " | W: " + str(self.buffer.workstation.id)
    #executes the event
    def execute(self):
        global c1_in, c1_list
        #collect buffer occupancy statistics
        self.buffer.totalCapacityMinutes += self.buffer.capacity * (self.time - self.buffer.timeOfLastCapacityChange)
        self.buffer.capacity += 1
        self.buffer.timeOfLastCapacityChange = self.time
        #if the workstation attached to this buffer is now able to assemble a product, make it immediately start assembling a product
        if self.buffer.workstation.hasComponentsReady() and self.buffer.workstation.busy == False:
            addToFEL(BeginAssemblyEvent(self.time, self.buffer.workstation))
        #make the inspector attached to this buffer immediately begin inspecting another component
        if self.buffer.inspector == INSPECTORS[0]:
            c1_in += 1
            c1_list.append(self.time)
            addToFEL(BeginInspectionEvent(self.time, self.buffer.inspector, COMPONENTS[0]))
        else:
            addToFEL(BeginInspectionEvent(self.time, self.buffer.inspector, getC2orC3(self.time)))
                
#defines an event type for when an inspector begins inspecting a component
class BeginInspectionEvent():
    #creates the event
    def __init__(self, time, inspector, component):
        self.inspector = inspector
        self.component = component
        self.time = time     
    #returns a description of the event
    def desc(self):
        return "BIE | t: " + str(self.time) + " | I: " + str(self.inspector.id) + " | C: " + str(self.component.id)
    #executes the event
    def execute(self):
        #generate an inspection time, and make this inspector finish inspecting this component after the inspection time
        inspection_time = getInspectionTime(self.inspector, self.component)
        addToFEL(FinishInspectionEvent(self.time + inspection_time, self.inspector, self.component))
        
#loop through which workstation gets C1
next_workstation_C1 = 1

#defines an event type for when an inspector finishes inspecting a component
class FinishInspectionEvent():
    #creates the event
    def __init__(self, time, inspector, component):
        self.inspector = inspector
        self.component = component
        self.time = time   
    #returns a description of the event
    def desc(self):
        return "FIE | t: " + str(self.time) + " | I: " + str(self.inspector.id) + " | C: " + str(self.component.id)
    #executes the event
    def execute(self):
        #find all buffers attached to this inspector with space for the component
        freeBuffers = self.inspector.getFreeBuffers(self.component)
        #if there is space, make the inspector put the component in one of the available buffers
        if len(freeBuffers) > 0:
            chosenBuffer = None

            if self.inspector.id == 2:
                for b in freeBuffers:
                    if chosenBuffer == None or chosenBuffer.capacity > b.capacity:
                        chosenBuffer = b

            #alternate which workstation gets C1 instead of using priorities
            global next_workstation_C1
            if self.inspector.id == 1:
                while chosenBuffer == None:
                    for b in freeBuffers:
                        if b.workstation.id == next_workstation_C1:
                            if chosenBuffer == None or chosenBuffer.capacity > b.capacity:
                                chosenBuffer = b
                    if next_workstation_C1 == 3: next_workstation_C1 = 1
                    else: next_workstation_C1 += 1                
            addToFEL(BufferFillEvent(self.time, chosenBuffer))
        #if there is no space, block the inspector
        else:
            self.inspector.waiting = self.component
            self.inspector.waitingSinceTime = self.time
        
#defines an event type for when a workstation begins assembling a product
class BeginAssemblyEvent():
    #creates the event
    def __init__(self, time, workstation):
        self.workstation = workstation
        self.time = time
    #returns a description of the event
    def desc(self):
        return "BAE | t: " + str(self.time) + " | W: " + str(self.workstation.id)
    #executes the event
    def execute(self):
        #iterate through all buffers attached to the workstation
        for b in self.workstation.getBuffers():
            #collect buffer occupancy statistics and remove components from buffers
            b.totalCapacityMinutes += b.capacity * (self.time - b.timeOfLastCapacityChange)
            b.capacity -= 1
            b.timeOfLastCapacityChange = self.time  
            #if the inspector attached to the buffer is blocked, unblock them and make them put a component in the buffer immediately
            if b.inspector.waiting == b.component:
                b.inspector.waiting = False
                b.inspector.totalWaitTime += self.time - b.inspector.waitingSinceTime
                addToFEL(BufferFillEvent(self.time, b))
        #make the workstation busy, generate an assembly time, and make the workstation finish assembling after the assembly time
        self.workstation.busy = True
        assembly_time = getAssemblyTime(self.workstation)
        self.workstation.totalBusyTime += assembly_time
        addToFEL(FinishAssemblyEvent(self.time + assembly_time, self.workstation))        
        
#defines an event type for when a workstation finishes assembling a product
class FinishAssemblyEvent():
    #creates the event
    def __init__(self, time, workstation):
        self.workstation = workstation
        self.time = time
    #returns a description of the event
    def desc(self):            
        return "FAE | t: " + str(self.time) + " | W: " + str(self.workstation.id)
    #executes the event
    def execute(self):
        global c1_out, c2_out, c3_out, c1_list, c2_list, c3_list, c1_times, c2_times, c3_times
        #if the buffers attached to the workstation contain enough components to assemble another product, make the workstation begin assembling a product immediately
        if self.workstation.hasComponentsReady():
            addToFEL(BeginAssemblyEvent(self.time, self.workstation))
        #if there are not enough components ready, make the workstation idle
        else:
            self.workstation.busy = False
        #collect completed product statistics
        self.workstation.productsCompleted += 1
        if self.workstation.id == 1:
            c1_out += 1
            c1_times.append(self.time - c1_list.pop(0))
        elif self.workstation.id == 2:
            c1_out += 1
            c1_times.append(self.time - c1_list.pop(0))
            c2_out += 1
            c2_times.append(self.time - c2_list.pop(0))
        elif self.workstation.id == 3:
            c1_out += 1
            c1_times.append(self.time - c1_list.pop(0))
            c3_out += 1
            c3_times.append(self.time - c3_list.pop(0))
            
class MeasureEvent():
    #creates the event
    def __init__(self, time):
        self.time = time
    #returns a description of the event
    def desc(self):            
        return "ME | t: " + str(self.time)
    #executes the event
    def execute(self):
        global c1_list, c2_list, c3_list, c1_samples, c2_samples, c3_samples
        #if the buffers attached to the workstation contain enough components to assemble another product, make the workstation begin assembling a product immediately
        c1_samples.append(len(c1_list))
        c2_samples.append(len(c2_list))
        c3_samples.append(len(c3_list))
            
#adds an event to the approprite position in the FEL based on its occurrence time
def addToFEL(event):
    for i in range(len(FEL)):
        if event.time < FEL[i].time:
            FEL.insert(i, event)
            return
    FEL.append(event)
    
#returns either the component C2 or C3 with an equal probability
def getC2orC3(time):
    global c2_in, c3_in, c2_list, c3_list
    component = COMPONENTS[random.randint(1,2)]
    if component == COMPONENTS[1]:
        c2_in += 1
        c2_list.append(time)
    else:
        c3_in += 1
        c3_list.append(time)
    return component

#retreives random inspection times sequentially from the correct file
def getInspectionTime(inspector, component):
    if inspector.id == 1:
        return getExponential(I1C1_lambda)
    elif component == COMPONENTS[1]:
        return getExponential(I2C2_lambda)
    else:
        return getExponential(I2C3_lambda)
            
#retreives random assembly times sequentially from the correct file
def getAssemblyTime(workstation):
    if workstation.id == 1:
        return getExponential(W1_lambda)
    elif workstation.id == 2:
        return getExponential(W2_lambda)
    else:
        return getExponential(W3_lambda)
        
#create the FEL
FEL = []

#create the inspectors, components, buffers, and workstations
INSPECTORS = [Inspector(1), Inspector(2)]
COMPONENTS = [Component(1), Component(2), Component(3)]
WORKSTATIONS = [Workstation(1), Workstation(2), Workstation(3)]
BUFFERS = [Buffer(WORKSTATIONS[0],INSPECTORS[0],COMPONENTS[0]), 
           Buffer(WORKSTATIONS[1],INSPECTORS[0],COMPONENTS[0]), 
           Buffer(WORKSTATIONS[1],INSPECTORS[1],COMPONENTS[1]), 
           Buffer(WORKSTATIONS[2],INSPECTORS[0],COMPONENTS[0]), 
           Buffer(WORKSTATIONS[2],INSPECTORS[1],COMPONENTS[2])]

#define the folder where inspection time and assembly time files are located
DATA_FOLDER = "data/"

#load the inspection and assembly times from the files in the DATA_FOLDER
I1C1_times = np.loadtxt(DATA_FOLDER + 'servinsp1.dat', unpack = True)
I2C2_times = np.loadtxt(DATA_FOLDER + 'servinsp22.dat', unpack = True)
I2C3_times = np.loadtxt(DATA_FOLDER + 'servinsp23.dat', unpack = True)
W1_times = np.loadtxt(DATA_FOLDER + 'ws1.dat', unpack = True)
W2_times = np.loadtxt(DATA_FOLDER + 'ws2.dat', unpack = True)
W3_times = np.loadtxt(DATA_FOLDER + 'ws3.dat', unpack = True)
I1C1_lambda = lam_estimator(I1C1_times)
I2C2_lambda = lam_estimator(I2C2_times)
I2C3_lambda = lam_estimator(I2C3_times)
W1_lambda = lam_estimator(W1_times)
W2_lambda = lam_estimator(W2_times)
W3_lambda = lam_estimator(W3_times)

#initialize the linear congruential generator
lin_con_gen = LinearCongruentialGenerator(289, 321, 65536, 0)

#get the user to enter a number of minutes that the simulation will run for
STOP_TIME = int(input("Enter the number of minutes to run the simulation: "))

#open the output file
OUTPUT_FILENAME = "output/simulation_output.txt"
output_file = open(OUTPUT_FILENAME, "w")

#Initialize the simulation by creating 2 BeginInspection events at time 0
#Each inspector should immediately begin inspecting a component when the simulation begins
FEL.append(BeginInspectionEvent(0, INSPECTORS[0], COMPONENTS[0]))
FEL.append(BeginInspectionEvent(0, INSPECTORS[1], getC2orC3(0)))

i = 0
while i < STOP_TIME:
    FEL.append(MeasureEvent(i))
    i += 10

#run the simulation until the FEL is empty or the STOP_TIME is reached
while len(FEL) > 0:
    #take the next event from the FEL
    event = FEL.pop(0)
    if event.time > STOP_TIME:
        break
    #record the event in the output file
    output_file.write(event.desc() + "\n")
    #execute the event
    event.execute()
    
#tell the user that the simulation has finished
output_file.write("SIMULATION FINISHED AT TIME " + str(STOP_TIME) + "\n")
print("SIMULATION FINISHED AT TIME", STOP_TIME)
print("SIMULATION OUTPUT STORED IN FILE \"", OUTPUT_FILENAME, "\"")

print("COMPONENT 1 ARRIVAL RATE:", c1_in / STOP_TIME)
print("COMPONENT 1 DEPARTURE RATE:", c1_out / STOP_TIME)
print("COMPONENT 1 AVERAGE TIME IN SYSTEM:", sum(c1_times) / len(c1_times))
print("COMPONENT 1 AVERAGE NUMBER IN SYSTEM:", sum(c1_samples) / len(c1_samples))
print("COMPONENT 2 ARRIVAL RATE:", c2_in / STOP_TIME)
print("COMPONENT 2 DEPARTURE RATE:", c2_out / STOP_TIME)
print("COMPONENT 2 AVERAGE TIME IN SYSTEM:", sum(c2_times) / len(c2_times))
print("COMPONENT 2 AVERAGE NUMBER IN SYSTEM:", sum(c2_samples) / len(c2_samples))
print("COMPONENT 3 ARRIVAL RATE:", c3_in / STOP_TIME)
print("COMPONENT 3 DEPARTURE RATE:", c3_out / STOP_TIME)
print("COMPONENT 3 AVERAGE TIME IN SYSTEM:", sum(c3_times) / len(c3_times))
print("COMPONENT 3 AVERAGE NUMBER IN SYSTEM:", sum(c3_samples) / len(c3_samples))

#collect the number of products completed by each workstation
total_products = 0
for w in WORKSTATIONS:
    output_file.write("Total P" + str(w.id) + " Finished: " + str(w.productsCompleted) + "\n")  
    print("Total P", w.id, "Finished:", w.productsCompleted)
    total_products += w.productsCompleted

#collect total throughput statistics
output_file.write("Total Throughput: " + str(total_products / STOP_TIME) + " products/min" + "\n")
print("Total Throughput:", total_products / STOP_TIME, "products/min")

#collect idle time statistics for each inspector
for i in INSPECTORS:
    output_file.write("Inspector " + str(i.id) + " Idle Time: " + str(100 * i.totalWaitTime / STOP_TIME) + " %" + "\n")
    print("Inspector", i.id, "Idle Time:", 100 * i.totalWaitTime / STOP_TIME, "%")
    
#collect average occupancy statistics for each buffer
for b in BUFFERS:
    output_file.write("Buffer " + str(b.inspector.id) + " " + str(b.workstation.id) + " Average Occupancy: " + str(b.totalCapacityMinutes / STOP_TIME) + "\n") 
    print("Buffer", b.inspector.id, b.workstation.id, "Average Occupancy:", b.totalCapacityMinutes / STOP_TIME)    
    
#collect busy time statistics for each workstation
for w in WORKSTATIONS:
    output_file.write("Workstation " + str(w.id) + " Busy Time: " + str(100 * w.totalBusyTime / STOP_TIME) + " %" + "\n")
    print("Workstation", w.id, "Busy Time:", 100 * w.totalBusyTime / STOP_TIME, "%") 
    
#close the output file
output_file.close()

