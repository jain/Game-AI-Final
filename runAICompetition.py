'''
 * Copyright (c) 2014, 2015 Entertainment Intelligence Lab, Georgia Institute of Technology.
 * Originally developed by Mark Riedl.
 * Last edited by Mark Riedl 05/2015
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
'''

import sys, pygame, math, numpy, random, time, copy
from pygame.locals import *

from constants import *
from utils import *
from core import *
from astarnavigator import *
from agents import *
from moba2 import *
from MyHero import *
from clonenav import *
from Castle import *
from AI import *
from buildBehaviors import *

############################
### How to use this file
###
### Use this file to simulate games between different behavior trees.
### Command: python runAICompetition.py

############################
### SET UP WORLD
import os
os.environ['SDL_VIDEODRIVER']='dummy'

x = 1400
y = 850
dims = (x, y)


########################
score = [0]* 12
for i in range(12):
	for j in range(i+1,12):
		print 'Behavior',i,'vs','behavior',j
		world = MOBAWorld(SEED, dims, dims, 0, 60)
		world.initializeTerrain([], (0, 0, 0), 4)
		agent = GhostAgent(ELITE, (x/2, y), 0, SPEED, world)
		world.setPlayerAgent(agent)
		p1 = BaseAI(world, 1)
		p1.behaviorTree = BuildBehavior(world,1,i)
		p2 = BaseAI(world, 2)
		p2.behaviorTree = BuildBehavior(world,2,j)
		world.setP1(p1)
		world.setP2(p2)
		world.debugging = False
		c1 = CastleBase(BASE, (180,y/2),world,1)
		c2 = CastleBase(BASE, (x-180,y/2),world,2)
		world.addCastle(c1)
		world.addCastle(c2)

		winner = world.runCompetition(500,False)
		if winner == 1:
			score[i] += 1
		else:
			score[j] += 1

print 'Scores: '
for i in range(12):
	print '   ',i,':',score[i]

