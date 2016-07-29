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
        self.change = 0
        self.read = json.load(open('data.txt'))
        self.last = 0
        self.lastR = ''
        self.gold = [0, 0]
        self.last_gold = [0, 0]
    
    def query(self, enemyBuilds, myBuilds, enemyGold, myGold):
        enemyCounts = numpy.zeros(len(BUILDTYPES) + len(MINIONTYPES)-1)
        for b in enemyBuilds:
            if type(b) in BUILDTYPES and type(b) is not Spawner:
                enemyCounts[BUILDTYPES.index(type(b))] += 1
            elif type(b) is Spawner:
                if b.minionType in MINIONTYPES:
                    enemyCounts[MINIONTYPES.index(b.minionType) + 3] += 1
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
        ratios = enemyCounts/float(max(enemyCounts))
        for i in range(0, len(ratios)):
            ratios[i] = round(ratios[i]*2.0)/2.0
        print ratios
        st = json.dumps(ratios.tolist())
        if self.change < 0:
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
        if st in self.read:
            a = json.loads(self.read[st])
            m = a.index(min(a))
            if m < 0:
                self.last = int(m)
                return self.last
        self.last = random.randint(0, 5)
        return self.last
