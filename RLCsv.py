import json
import random
from Castle import AttackBooster, GoldMiner, Defense, Spawner
from Minions import TankMinion, AoEMinion, ADCMinion
import numpy

BUILDTYPES = [AttackBooster, GoldMiner, Defense, Spawner]
MINIONTYPES = [TankMinion, AoEMinion, ADCMinion]


'''
class takes care of reinforcement learning
we store the data in data.txt and use that to make the next action
'''
class RLCsv():
    # instantiate necessary variables and create the data storage file
    def __init__(self):
        self.gold_ratio = 1.0
        self.change = 0
        try:
            self.read = json.load(open('data.txt'))
        except:
            self.read = {}
        self.last = 0
        self.lastR = ''
        self.gold = [0, 0]
        self.last_gold = [0, 0]
    # based on curr scenario choose the best action to take
    def query(self, enemyBuilds, myBuilds, enemyGold, myGold):
        enemyCounts = numpy.zeros(len(BUILDTYPES) + len(MINIONTYPES)-1)
        # get each of the type of buildings.
        for b in myBuilds:
            if type(b) in BUILDTYPES and type(b) is not Spawner:
                enemyCounts[BUILDTYPES.index(type(b))] += 1
            elif type(b) is Spawner:
                if b.minionType in MINIONTYPES:
                    enemyCounts[MINIONTYPES.index(b.minionType) + 3] += 1
        # compute the total gold per player
        if myGold < self.last_gold[0]:
            self.gold[0] += 10
        else:
            self.gold[0] += (myGold-self.last_gold[0])
        self.last_gold[0] = myGold
        if enemyGold < self.last_gold[1]:
            self.gold[1] += 10
        else:
            self.gold[1] += (enemyGold-self.last_gold[1])
        self.last_gold[1] = enemyGold
        print str([myGold, enemyGold, self.gold[0], self.gold[1]])
        myGold = self.gold[0]
        enemyGold = self.gold[1]
        # self.change is the reward
        self.change = (myGold - enemyGold) - self.change
        print self.change
        self.gold_ratio = (float(myGold)/enemyGold)
        # compute ratio of buildings
        ratios = enemyCounts/float(max(enemyCounts))
        for i in range(0, len(ratios)):
            ratios[i] = round(ratios[i]*4.0)/4.0
        print ratios
        st = json.dumps(ratios.tolist())
        # save the data
        if self.lastR not in self.read:
            arr = [[10, 10], [10, 10], [10, 10],[10, 10], [10, 10], [10, 10]]
            arr[self.last].append(self.change)
            self.read[self.lastR] = json.dumps(arr)
        else:
            a = json.loads(self.read[self.lastR])
            a[self.last].append(self.change)
            a[self.last][0] = float(sum(a[self.last][1:]))/len(a[self.last])
            self.read[self.lastR] = json.dumps(a)
        json.dump(self.read, open('data.txt', 'w'))
        self.lastR = st
        # read data and choose best action to take
        if st in self.read:
            a = json.loads(self.read[st])
            m = a.index(min(a))
            if m < 0:
                self.last = int(m)
                return self.last
        # if no action is possible choose a random number
        self.last = random.randint(0, 5)
        return self.last
