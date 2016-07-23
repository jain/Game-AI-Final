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
from Castle import *
from math import sqrt
from BaseMinion import *
from MinionB import *

ATTACK_ORDER = [MinionB, BaseMinion, Building, CastleBase]
MYHITPOINTS = 20
MYSPEED = (5, 5)
MYFIRERATE = 50
BULLETRANGE = 250
BULLETDAMAGE = 10
BULLETSPEED = (20, 20)
BULLET = "sprites/bullet2.gif"
AREAEFFECTDAMAGE = 25
AREAEFFECTRANGE = 50

##########################

class AoEBullet(MOBABullet):
	### range: how far the bullet will travel before expiring

	def __init__(self, position, orientation, world, image=BULLET, speed=BULLETSPEED,
				 damage=BULLETDAMAGE, range=BULLETRANGE):
		MOBABullet.__init__(self, position, orientation, world, image, speed, damage, range)

	def update(self, delta):
		Bullet.update(self, delta)
		if self.distanceTraveled > self.range:
			self.speed = (0, 0)
			self.explode()
			self.world.deleteBullet(self)

	def collision(self, thing):
		Bullet.collision(self, thing)
		if isinstance(thing, MOBAAgent) and (thing.getTeam() == None or thing.getTeam() != self.owner.getTeam()):
			self.explode()
			self.hit(thing)
		if isinstance(thing, Building) and (thing.getTeam() == None or thing.getTeam() != self.owner.getTeam()):
			self.explode()
			self.hit(thing)
		elif isinstance(thing, CastleBase) and (thing.getTeam() == None or thing.getTeam() != self.owner.getTeam()):
			self.explode()
			self.hit(thing)
	
	def explode(self):
		pygame.draw.circle(self.world.background, (255, 0, 0), (int(self.getLocation()[0]), int(self.getLocation()[1])), AREAEFFECTRANGE, 1)
		team = self.owner.getTeam()
		for x in self.world.getEnemyNPCs(team) + self.world.getEnemyBases(team) + self.world.getEnemyTowers(team):
			if withinRange(self.getLocation(), x.getLocation(), AREAEFFECTRANGE):
				x.damage(AREAEFFECTDAMAGE)

##########################

class MinionC(BaseMinion):
    def __init__(self, position, orientation, world, image=ELITE, speed=MYSPEED, viewangle=360, hitpoints=MYHITPOINTS,
                 firerate=MYFIRERATE, bulletclass=AoEBullet):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.states = [Idle, Move, Attack]
        self.world = world
        self.position = position
        self.bullet = bulletclass
        self.bullet_range = bulletclass((0,0),0,None).range

    def start(self):
        BaseMinion.start(self)
        self.changeState(Idle)

############################

ATTACK_ORDER = [MinionB, BaseMinion, Building, CastleBase]

############################
### Idle
###
### This is the default state of MyMinion. The main purpose of the Idle state is to figure out what state to change to and do that immediately.

class Idle(State):
    
    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()

    def execute(self, delta=0):
        State.execute(self, delta)
        agent = self.agent
        pos = agent.getLocation()
        
        # Following ATTACK_ORDER listing, look for nearby agents and attack closest, highest priority target
        for type in ATTACK_ORDER:
            agents = sorted([(distance(x.getLocation(), pos), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), pos, BULLETRANGE)])
            if len(agents) > 0:
                agent.changeState(Attack, agents[0][1])
        
        # If no enemy is within range and enemy buildings are still alive, move towards the nearest one
        bases = sorted([(distance(x.getLocation(), pos), x) for x in agent.world.getEnemyBuildings(agent.getTeam())])
        if len(bases) > 0:
            agent.changeState(Move, bases[0][1].getLocation())
        
        # If no enemy is within range and enemy castles are still alive, move towards the nearest one
        bases = sorted([(distance(x.getLocation(), pos), x) for x in agent.world.getEnemyCastles(agent.getTeam())])
        if len(bases) > 0:
            agent.changeState(Move, bases[0][1].getLocation())
        
        # Else, do nothing
        return None


##############################

### Move
###
### Agent is not within range of anything attackable
### Moves toward goal until it reaches something attackable and within range

class Move(State):

    def parseArgs(self, args):
        # Set navigation to parsed location
        self.agent.navigateTo(args[0])
    
    def execute(self, delta = 0):
        agent = self.agent        
        # Following ATTACK_ORDER listing, look for nearby agents and attack closest, highest priority target
        for type in ATTACK_ORDER:
            agents = sorted([(distance(x.getLocation(), agent.getLocation()), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), agent.getLocation(), BULLETRANGE)])
            if len(agents) > 0:
                agent.changeState(Attack, agents[0][1])

##############################

### Attack
###
### State reached when agent is within range of an enemy
### Agent is given target to attack via arguments

class Attack(State):

    def parseArgs(self, args):
        self.victim = args[0]

    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()

    def execute(self, delta = 0):
        agent = self.agent
        # Check that victim exists and is not already dead or now out of range
        if self.victim is not None and self.victim in agent.getVisible() and withinRange(agent.getLocation(), self.victim.getLocation(), BULLETRANGE):
            agent.turnToFace(self.victim.getLocation())
            agent.shoot()
        # If target is dead or out of range, switch back to idle
        else:
            agent.changeState(Idle)
        # If after shooting and target is not dead, but a higher priority target is nearby, switch targets
        for type in ATTACK_ORDER[:-1]:
            if isinstance(self.victim, type):
                break
            else:
                agents = sorted([(distance(x.getLocation(), agent.getLocation()), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), agent.getLocation(), SMALLBULLETRANGE)])
                if len(agents) > 0:
                    #agent.changeState(Attack, agents[0][1])
                    self.victim = agents[0][1]

##############################