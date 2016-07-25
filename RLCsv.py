import json
import random
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

class RLCsv():
    def __init__(self):
        self.gold_ratio = 1.0
        self.change = 100000
        self.read = json.load(open('data.txt'))
        self.types = ['a', 'g', 'd', 'tank', 'aoe', 'adc']
        self.last = 0
        self.lastR = ''
    def query(self, bs1, bs2, gold):
        d1 = {}
        d2 = {}
        for t in self.types:
            d1[t] = 0
            d2[t] = 0
        for b in bs1:
            if b in d1:
                d1[b] = d1[b] + 1
        for b in bs2:
            if b in d2:
                d2[b] = d2[b] + 1
        self.ratios = []
        for t in self.types:
            ratio = -1.0
            try:
                ratio = float(d2[t])/d1[t]
            except:
                pass
            self.ratios.append(ratio)
        self.change = (float(gold[1])/gold[0]) - self.gold_ratio
        self.gold_ratio = (float(gold[1])/gold[0])
        self.ratios.append(self.gold_ratio)
        for i in range(0, len(self.ratios)):
            round(self.ratios[i]*2.0)/2.0
        st = json.dumps(self.ratios)
        if self.change > -10:
            '''if not self.lastR in self.read:
                self.read[self.lastR] = self.change
            else:'''
            a = {}
            a[self.last] = self.change
            self.read[self.lastR] = a#(self.read[self.lastR]+self.change)/2.0
            json.dump(self.read, open('data.txt', 'w'))
        self.lastR = st
        if (st in self.read):
            m = max(self.read[st])
            if m >0:
                self.last = int(m)
                return self.last
        self.last = random.randint(0, 5)
        return self.last
