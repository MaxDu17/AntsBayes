#Maximilian Du and Matthew Schuck
#Ant House-Hunting Simulation Code
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt 
import math
from matplotlib.animation import FuncAnimation 
import matplotlib.animation as animation 

INITIAL = 10000 #large initial variance to approximate a uniform distribution 
OBSERVATION_ERROR = 1 #standard deviation of observation distribution (known to the ants)
class Ant():
    def __init__(self, quality_list, ax = None, anim = False):
        self.num_locs = len(quality_list)
        self.means = np.zeros(shape=(self.num_locs))
        self.vars = np.zeros(shape=(self.num_locs))
        self.vars.fill(INITIAL)
        self.quality_list = quality_list #these are the true qualities of the locations. They are not used by the ants themselves.
        
        self.location = 0
        self.lastObservation = 0 
        
        self.isRecruited = False #indicates if an ant is a follower
        self.toCompare = None #this is the leader ant

        self.isRecruiting = False #indicates if an ant is a leader
        self.previousHome = None #this is where the leader came from

        self.lines = list() #for animation 

        if anim: #for animation purposes
            for i in range(self.num_locs):
                self.lines.append(ax.plot([], [])[0])

            self.x = np.linspace(-1, 10, 200)
            self.ax = ax
            self.ax.set_xlim(-1, 10)
            self.ax.set_ylim(0, 5)
            self.ax.grid(True)
            self.ax.set(title = "Simulation 1: Single Ant Prior Distributions." + " Step " + str(0))


    def _sampleFrom(self): #Thomson sampling 
        val_list = [norm.rvs(loc = self.means[i], scale = math.sqrt(self.vars[i])) for i in range(self.num_locs)]
        return np.argmax(val_list)
    
    def _observe(self, location): #observe from the location
        return norm.rvs(loc = self.quality_list[location], scale = OBSERVATION_ERROR)
    
    def _update(self, location, observation): #Update prior beliefs using Kalman filter
        normalization = (1 / self.vars[location]) + (1 / OBSERVATION_ERROR**2)
        self.means[location] = ((observation / OBSERVATION_ERROR**2) + (self.means[location] / self.vars[location])) / normalization
        self.vars[location] = 1 / normalization 
    
    def return_distributions(self): #for diagnostics 
        return self.means, self.vars 

    def __call__(self, i): #for simulation a's line animation
        location_to_visit = self._sampleFrom()
        observation = self._observe(location_to_visit)
        self._update(location_to_visit, observation)
        y = norm.pdf(self.x, self.means[location_to_visit], math.sqrt(self.vars[location_to_visit]))
        self.lines[location_to_visit].set_data(self.x, y)
        self.ax.set(title = "Simulation 1: Single Ant Prior Distributions. " + "Step " + str(i))
        return self.lines
    
    def step(self):
        location_to_visit = self._sampleFrom() #thomson sampling here
        if self.isRecruited: 
            self.isRecruited = False #reset recuit status once we compre
            if self.toCompare.getEstimate(self.toCompare.previousHome) > self.means[self.location]:
                location_to_visit = self.toCompare.previousHome #we follow the lead if it provides a better value
        
        if self.isRecruiting:
            self.isRecruiting = False
            location_to_visit = self.previousHome #return back to where we were

        observation = self._observe(location_to_visit) #observe the location we want to visit
        self.lastObservation = observation 
        self.location = location_to_visit #keep track of location
        self._update(location_to_visit, observation)
        return observation
    
    def getEstimate(self, location): #diagnostic function 
        return self.means[location]

    def recruit(self, ant): #flags this ant as a follower
        assert not(self.isRecruited) #makes sure that we are not doubly-recruiting an ant
        self.isRecruited = True
        self.toCompare = ant 
    
    def setRecruiting(self, ant): #flags this ant as a leader
        assert not(self.isRecruiting) #makes sure that we are not doubly-making this ant a recruiter
        self.isRecruiting = True #mark leader
        self.previousHome = self.location #save current location 
        self.location = ant.location #move leader to follower


class AntColony(): #encapsulates a bunch of ants and incorporates quorum + tandem running 
    def __init__(self, numAnts, quality_list, p_quorum, ax = None, anim = False, tandem = False, tandem_threshold = 1000):
        self.antsList = list()
        self.distribution = np.zeros(shape = len(quality_list))
        self.distribution[0] = numAnts #initialize all ants at location 0
        self.tandem_threshold = tandem_threshold
        for i in range(numAnts): #initialize ants
            self.antsList.append(Ant(quality_list))
        self.p_quorum = p_quorum
        self.first = True
        self.tandem = tandem
        self.tandemCounter = 0

        self.finalLocation = -1 #stores the location where convergence happens 

        if anim:
            self.ax = ax
            self.barcollection = self.ax.bar(range(len(quality_list)), self.distribution)
            # self.ax.set(title = "Simulation 2: Ant Colony With Quorum Enabled. Step 0")
    
    def step(self, i):
        #uncomment this to enable immediate termination on quorum
        # if not self.first and np.max(self.distribution) > self.p_quorum * np.sum(self.distribution): 
        #     self.finalLocation = np.argmax(self.distribution)
        #     return True
        if not self.first and np.max(self.distribution) == len(self.antsList):
            return True #returns True if convergence is reached 
        prob_list = self.distribution / np.sum(self.distribution)
        for ant_num, ant in enumerate(self.antsList):
            if self.first or prob_list[ant.location] < self.p_quorum: #selects ants that currently can move
                stepStatus = ant.isRecruited or ant.isRecruiting #we don't want tandem pairs to "bounce"
                self.distribution[ant.location] -= 1
                observation = ant.step() #moves ants to their next locations
                self.distribution[ant.location] += 1
                #this is the code that enables tandem-running
                if i > 5 and self.tandem and observation > self.tandem_threshold and not(stepStatus): 
                    roughList = self.antsList[0:ant_num] #it is very tricky if the follower happens after the leader. So we don't address it.
                    refinedList = [thisant for thisant in roughList if thisant.location != ant.location and not(thisant.isRecruited) 
                    and not(thisant.isRecruiting)] #basically select all valid candidates for followers
                    if len(refinedList) == 0: 
                        continue
                    target = refinedList[np.random.randint(0, len(refinedList))] #select ant at random
                    self.distribution[ant.location] -= 1
                    target.recruit(ant) #mark follower 
                    ant.setRecruiting(target) #mark leader
                    self.distribution[ant.location] += 1
                    self.tandemCounter += 1
            if prob_list[ant.location] > self.p_quorum:
                ant.isRecruited = False #this does not affect anything, but in our animation we need to clear statuses in quorumed ants
                ant.isRecruiting = False 
                ant.lastObservation = 0
        if self.first: #"first" basically allows us to start at a set location
            self.first = False
        return False

    def __call__(self, i): #for animation; the same code but with bargraphs 
        self.ax.set(title = "Simulation 2: Ant Colony With Tandem Enabled, Quorum Disabled. Step " + str(i))
        prob_list = self.distribution / np.sum(self.distribution)
        for ant_num, ant in enumerate(self.antsList):
            if self.first or prob_list[ant.location] < self.p_quorum:
                stepStatus = ant.isRecruited or ant.isRecruiting #basically, we don't want tandem pairs to "bounce"
                self.distribution[ant.location] -= 1
                observation = ant.step() 
                self.distribution[ant.location] += 1
                if i > 5 and self.tandem and observation > self.tandem_threshold and not(stepStatus): 
                    roughList = self.antsList[0:ant_num]
                    refinedList = [thisant for thisant in roughList if thisant.location != ant.location and not(thisant.isRecruited) 
                    and not(thisant.isRecruiting)]
                    if len(refinedList) == 0:
                        continue
                    target = refinedList[np.random.randint(0, len(refinedList))]
                    self.distribution[ant.location] -= 1
                    target.recruit(ant)
                    ant.setRecruiting(target)
                    self.distribution[ant.location] += 1
                    self.tandemCounter += 1
            if prob_list[ant.location] > self.p_quorum:
                ant.isRecruited = False
                ant.isRecruiting = False 
                ant.lastObservation = 0

        for i, b in enumerate(self.barcollection):
            b.set_height(self.distribution[i])

        if self.first:
            self.first = False
        
        return self.barcollection
    
    def return_dist_matrix(self, steps): #returns an n X m matrix where n is the # steps and m is the number of locations
        dist_list = list()
        for i in range(steps):
            self.step(i)
            dist_list.append(self.distribution.copy())
        return dist_list

    def return_ant_matrix(self, steps): #returns an n X k matrix where n is the # steps and k is the number of ants 
        dist_list = list()
        for i in range(steps):
            self.step(i)
            antsList = [ant.location for ant in self.antsList]
            dist_list.append(antsList)
        return dist_list

    def verify_distribution(self): #sanity check: make sure that the distribution matches what the ants really are
        distribution_to_test = np.zeros(shape = len(self.distribution))
        for ant in self.antsList:
            distribution_to_test[ant.location] += 1
        print(distribution_to_test)
        print(self.distribution)


    def master_info_dump(self, steps): #messy function that we use to interface with our animation software
        distribution_list = list()
        ants_list = list()
        collective_posterior_means = list()
        collective_posterior_vars = list()
        observation_values = list()
        tandemDict = {}
        convergence_step = -1
        for i in range(steps):
            #calculate distribution and ant lists
            if self.step(i) and convergence_step == -1:
                convergence_step = i
            distribution_list.append(self.distribution.copy())
            curr_ants_dist = [ant.location for ant in self.antsList]
            ants_list.append(curr_ants_dist)

            #calculate the means and variances
            means = np.zeros(len(self.distribution))
            vars = np.zeros(len(self.distribution))
            for ant in self.antsList:
                means = means + ant.means
                vars = vars + ant.vars
            means /= len(self.distribution)
            vars /= (len(self.distribution)**2)
            collective_posterior_means.append(means)
            collective_posterior_vars.append(vars)

            #record observations
            obs = [ant.lastObservation for ant in self.antsList]
            observation_values.append(obs)

            #record tandem pairs 
            tup_list = list()
            explored = list()
            for thisAntIndex, ant in enumerate(self.antsList):
                if ant.isRecruited:
                    assert ant.toCompare.location != ant.toCompare.previousHome
                    assert ant.isRecruited != ant.isRecruiting
                    assert thisAntIndex not in explored
                    explored.append(thisAntIndex)
                    if ant.toCompare.getEstimate(ant.toCompare.previousHome) > ant.means[ant.location]:
                        tup = (thisAntIndex, self.antsList.index(ant.toCompare), ant.location, ant.toCompare.previousHome)
                        tup_list.append(tup)
            tandemDict[i] = tup_list


        return distribution_list, ants_list, collective_posterior_means, collective_posterior_vars, observation_values, tandemDict, convergence_step
            



locations_list = [1.1, 1.2, 1.4, 2, 1.4] 

def simulation_a(): #runs simulation 1 animation 
    fig, ax = plt.subplots()
    ant_obj = Ant(locations_list, ax, anim = True)
    anim = FuncAnimation(fig, ant_obj, frames = 200, interval = 200, blit = True) 
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=15, bitrate=1280)
    fig.set_size_inches(8, 8, True)
    # plt.show() #uncomment to animate. Comment to record 
    anim.save("simulation_a.mp4", writer=writer)
    

def simulation_b(): #runs simulation 2 animation 
    fig, ax = plt.subplots()
    colony = AntColony(100, locations_list, 0.6, ax, anim = True)
    anim = FuncAnimation(fig, colony, frames = 200, interval = 200, blit = True)
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=15, bitrate=1280)
    fig.set_size_inches(8, 8, True)
    anim.save("simulation_b.mp4", writer=writer, dpi = 300)
    # plt.show() #uncomment to animate. Comment to record 

def simulation_c():
    fig, ax = plt.subplots()
    colony = AntColony(100, locations_list, 1, ax, anim = True, tandem = True, tandem_threshold = 1.5)
    anim = FuncAnimation(fig, colony, frames = 400, interval = 400, blit = True)
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=15, bitrate=1280)
    fig.set_size_inches(8, 8, True)
    anim.save("simulation_c_noquorum.mp4", writer=writer, dpi = 300)
    # plt.show() #uncomment to animate, comment to record 

def make_matrix_a(): #constructs things needed to animate the first simulation 
    ant_obj = Ant(locations_list)
    location_list = list()
    means_list = list()
    vars_list = list()
    obs_list = list()
    for i in range(300):
        ant_obj.step()
        location_list.append(ant_obj.location)
        means_list.append(ant_obj.means.copy())
        vars_list.append(ant_obj.vars.copy())
        obs_list.append(ant_obj.lastObservation)

    return location_list, means_list, vars_list, obs_list

def make_matrix_b(): #ant locations for simulation 2 
   colony = AntColony(100, locations_list, 0.6) 
   return colony.return_ant_matrix(100)

def make_matrix_c(): #ant locaitons for simulation 3 
   colony = AntColony(100, locations_list, 0.6, tandem = True, tandem_threshold = 1.5)
   return colony.return_ant_matrix(250)

def countSims(colony): #sanity checking function that runs the model and prints out the distribution 
    status = False
    counter = 0
    while not(status):
        status = colony.step(counter)
        counter += 1
        print(colony.distribution)
        print(counter)
    print(counter)
    return counter, colony.finalLocation

def sweep_quorum_accuracy(): #code used to generate accuracy vs quorum level 
    values = list()
    x = np.linspace(0.1, 0.5, 20)
    print(x)
    for i in x:
        correctCounter = 0
        for j in range(30):
            colony = AntColony(100, locations_list, i, tandem = True, tandem_threshold = 1.5)
            steps, location = countSims(colony)
            if location == np.argmax(locations_list):
                correctCounter += 1
        print("\t", correctCounter)
        values.append(correctCounter / 30)
    print(values)
    plt.plot(x, values,'o-r')
    plt.axis([0.1, 0.5, 0, 1.1])
    plt.title("Quorum Accuracy vs Quorum Level (t = 1.5)")
    plt.show()

def sweep_parameter(): #code used to generate any sort of function sweeps 
    values = list()
    x = np.linspace(0.1, 0.5, 20)
    print(x)
    for i in x: #change me 
        colony = AntColony(100, locations_list, i, tandem = True, tandem_threshold = 1.5)
        steps, location = countSims(colony)
        values.append(steps)
    print(values)
    plt.plot(x, values,'o-r')
    plt.axis([0.1, 0.5, 0, 1.1])
    plt.title("a vs b (t = 1.5)")
    plt.show()

def distribution(): #code that generates a distribution of convergence steps 
    num_shots = 150
    values = np.zeros(num_shots)
    for i in range(num_shots):
        colony = AntColony(100, locations_list, 0.6, tandem = True, tandem_threshold = 1.5)
        values[i] = countSims(colony)
    plt.hist(values, bins = 20, range = (0, 100))
    plt.title("Tandem Convergence Distribution (q = 0.6, t = 1.5)")
    plt.show()

def getAllData(): #code that we call to get the information needed for animation 
    colony = AntColony(100, locations_list, 0.6, tandem = True, tandem_threshold = 1.5)
    return colony.master_info_dump(50)

# simulation_c()
print(countSims(AntColony(100, locations_list, 0.6, tandem = True, tandem_threshold = 1.5)))
# print(getAllData())
