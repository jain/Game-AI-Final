import json
import random
from Castle import AttackBooster, GoldMiner, Defense, Spawner
from Minions import TankMinion, AoEMinion, ADCMinion
import numpy
'''import itertools

vals = [0.0, 0.5, 1.0, 1.5, 2.0]

rlDict= {}

for prod in itertools.product(vals, repeat=7):
    rlDict[json.dumps(prod)] = -0.5
json.dump(rlDict, open('data.txt', 'w'))'''
'''
rlDict = json.load(open('data.txt'))

for key, val in rlDict.iteritems():
    print key
    print json.loads(key)
'''

BUILDTYPES = [AttackBooster, GoldMiner, Defense, Spawner]
MINIONTYPES = [TankMinion, AoEMinion, ADCMinion]

class RLCsv():
    def __init__(self):
        self.gold_ratio = 1.0
        self.change = 100000
        self.read = json.load(open('data.txt'))
        self.last = 0
        self.lastR = ''
    
    def query(self, myBuilds, enemyBuilds, myGold, enemyGold):
        myCounts = numpy.zeros(len(BUILDTYPES) + len(MINIONTYPES) - 1)
        enemyCounts = numpy.zeros(len(BUILDTYPES) + len(MINIONTYPES) - 1)
        for b in myBuilds:
            if type(b) in BUILDTYPES and type(b) is not Spawner:
                myCounts[BUILDTYPES.index(type(b))] += 1
            elif type(b) is Spawner:
                if b.minionType in MINIONTYPES:
                    myCounts[MINIONTYPES.index(b.minionType) + 3] += 1
        for b in enemyBuilds:
            if type(b) in BUILDTYPES and type(b) is not Spawner:
                enemyCounts[BUILDTYPES.index(type(b))] += 1
            elif type(b) is Spawner:
                if b.minionType in MINIONTYPES:
                    enemyCounts[MINIONTYPES.index(b.minionType) + 3] += 1
        
        ratios = []
        for i in xrange(len(ratios)):
            ratio = -1.0
            try:
                ratio = float(myCounts[i])/enemyCounts[i]
            except:
                pass
            ratios.append(ratio)
        self.change = (float(myGold)/enemyGold) - self.gold_ratio
        self.gold_ratio = (float(myGold)/enemyGold)
        ratios.append(self.gold_ratio)
        
        for i in range(0, len(ratios)):
            ratios[i] = round(ratios[i]*2.0)/2.0
        st = json.dumps(ratios)
        if self.change > -10:
            '''if not self.lastR in self.read:
                self.read[self.lastR] = self.change
            else:'''
            a = {}
            a[self.last] = self.change
            self.read[self.lastR] = a #(self.read[self.lastR]+self.change)/2.0
            json.dump(self.read, open('data.txt', 'w'))
        self.lastR = st
        if (st in self.read):
            m = max(self.read[st])
            if m > 0:
                self.last = int(m)
                return self.last
        self.last = random.randint(0, 5)
        return self.last
