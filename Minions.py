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
from math import *

## BASEMINION'S CONSTANTS ##
GROUPING_RANGE = 200
ALIGNMENT_WEIGHT = 4
COHESION_WEIGHT = 12
SEPARATION_WEIGHT = 12
INFLUENCE_PERCENT = 0.5

## MINION A'S CONSTANTS ##
SPEED_A = (5, 5)
HITPOINTS_A = 25
FIRERATE_A = 10
BULLET_A = "sprites/bullet.gif"
BULLETSPEED_A = (20, 20)
BULLETDAMAGE_A = 1
BULLETRANGE_A = 150

## MINION B'S CONSTANTS ##
SPEED_B = (3, 3)
HITPOINTS_B = 100
FIRERATE_B = 20
BULLET_B = "sprites/bullet.gif"
BULLETSPEED_B = (20, 20)
BULLETDAMAGE_B = 3
BULLETRANGE_B = 25

## MINION C'S CONSTANTS ##
SPEED_C = (5, 5)
HITPOINTS_C = 15
FIRERATE_C = 80
BULLET_C = "sprites/bullet2.gif"
BULLETSPEED_C = (15, 15)
BULLETDAMAGE_C = 5
BULLETRANGE_C = 250
AREAEFFECTRANGE_C = 50

## MINION D'S CONSTANTS ##
SPEED_D = (2, 2)
HITPOINTS_D = 50
FIRERATE_D = 100
BULLET_D = "sprites/bullet2.gif"
BULLETDAMAGE_D = 10
BULLETRANGE_D = 50

############################

# BASE MINION CLASS

############################

class BaseMinion(Minion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED, viewangle=360, hitpoints=HITPOINTS,
                 firerate=FIRERATE, bulletclass=SmallBullet, attackorder = []):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.grouping_range = GROUPING_RANGE
        self.states = [Idle, Move, Attack]
        self.world = world
        self.position = position
        self.bullet = bulletclass
        self.bullet_range = bulletclass((0,0),0,None).range
        self.attackorder = attackorder

    def start(self):
        Minion.start(self)
        self.changeState(Idle)
    
    def getAlignmentVector(self, nearby):
        # Set default orientation
        v = self.orientation
        # For each ally nearby, add their orientation to the group value
        for ally in nearby:
            v = numpy.add(v, ally.orientation)
        # Divide the collective orientation value, then return the vector form
        v = numpy.divide(v, len(nearby) + 1)
        vec = [cos(radians(v)), sin(radians(v))]
        return vec
    
    def getCohesionVector(self, nearby):
        # Set default position of center of mass
        v = [0, 0]
        # For each ally nearby, add their location to the center of mass
        for ally in nearby:
            v = numpy.add(v, ally.getLocation())
        # Divide sum of mass by number of allies for actual center of mass
        v = numpy.divide(v, len(nearby))
        # Find difference from self position, return normalized vector
        v = numpy.subtract(v, self.getLocation())
        v = numpy.divide(v, vectorMagnitude(v))
        return v
    
    def getSeparationVector(self, nearby):
        # Set default position of separation offset
        v = [0, 0]
        # For each ally, add the translational difference between them and self to offset
        for ally in nearby:
            dropoff = 1 - distance(ally.getLocation(), self.getLocation())/self.grouping_range
            v = numpy.multiply(numpy.add(v, numpy.subtract(ally.getLocation(), self.getLocation())), dropoff)
        # Divide total offset by number of agents nearby
        v = numpy.divide(v, len(nearby))
        #v = numpy.subtract(v, self.getLocation())
        # Find opposite vector and return normalization of it
        v = numpy.multiply(v, -1)
        v = numpy.divide(v, vectorMagnitude(v))
        return v
    
    def getInfluenceVector(self):
        # Get list of all allies within grouping range
        nearby = [n for n in self.world.getNPCsForTeam(self.team) if n != self and withinRange(self.position, n.getLocation(), self.grouping_range)]
        # If no allies are close enough, we return nothing
        if len(nearby) == 0:
            return [0, 0]
        # Get alignment, cohesion, and separation vectors, take their weights, and sum them together
        a = self.getAlignmentVector(nearby)
        c = self.getCohesionVector(nearby)
        s = self.getSeparationVector(nearby)
        v = numpy.add(numpy.multiply(a, ALIGNMENT_WEIGHT), numpy.multiply(c, COHESION_WEIGHT))
        v = numpy.add(v, numpy.multiply(s, SEPARATION_WEIGHT))
        # Normalize if able and return the vector
        v = numpy.divide(v, ALIGNMENT_WEIGHT + COHESION_WEIGHT + SEPARATION_WEIGHT)
        v = [m*n*INFLUENCE_PERCENT for m,n in zip(v, self.speed)]
        return v

    def update(self, delta):
        Mover.update(self, delta)
        if self.moveTarget is not None:
            drawCross(self.world.background, self.moveTarget, (0, 0, 0), 5)
            direction = [m - n for m,n in zip(self.moveTarget,self.position)]
            # Figure out distance to moveTarget
            #mag = reduce(lambda x, y: (x**2)+(y**2), direction)**0.5 
            mag = distance(self.getLocation(), self.moveTarget)
            if mag < self.getRadius()/2.0: #min(self.rect.width,self.rect.height)/2.0:
                # Close enough
                self.moveTarget = None
                self.moveOrigin = None
                if self.navigator != None:
                    self.navigator.doneMoving()
                    self.doneMoving()
            else:
                # Move
                normalizedDirection = [x/mag for x in direction]
                #direction = numpy.add(normalizedDirection, self.getInfluenceVector())
                #normalizedDirection = [x/vectorMagnitude(direction) for x in direction]
                targetDistance = numpy.subtract(self.moveTarget, self.getLocation())
                next = [m*n for m,n in zip(normalizedDirection,self.speed)]
                if all(abs(a) < abs(b) for a,b in zip(targetDistance, next)):
                    next = targetDistance
                #normalizedDirection = [x/mag for x in direction]
                #next = [m*n for m,n in zip(normalizedDirection,self.speed)]
                next = numpy.add(next, self.getInfluenceVector())
                self.distanceTraveled = self.distanceTraveled + distance((0,0), next)
                self.move(next)
                self.navigator.update(delta)
                # Check for shortcut
                if self.navigator != None:
                    self.navigator.smooth()
        if self.canfire == False:
            self.firetimer = self.firetimer + 1
            if self.firetimer >= self.firerate:
                self.canfire = True
                self.firetimer = 0
        StateMachine.update(self, delta)
        # Ask the world for what is visible (Movers) within the cone of vision
        visible = self.world.getVisible(self.getLocation(), self.orientation, self.viewangle)
        self.visible = visible
        return None

############################

# STATES FOR BASEMINION

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
        for type in agent.attackorder:
            agents = sorted([(distance(x.getLocation(), pos), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), pos, agent.bullet_range)])
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


############################

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
        if agent.getMoveTarget() == None:
            agent.changeState(Idle)
        # Following ATTACK_ORDER listing, look for nearby agents and attack closest, highest priority target
        for type in agent.attackorder:
            agents = sorted([(distance(x.getLocation(), agent.getLocation()), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), agent.getLocation(), agent.bullet_range)])
            if len(agents) > 0:
                agent.changeState(Attack, agents[0][1])

############################

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
        if self.victim is not None and self.victim in agent.getVisible() and withinRange(agent.getLocation(), self.victim.getLocation(), agent.bullet_range):
            agent.turnToFace(self.victim.getLocation())
            agent.shoot()
        # If target is dead or out of range, switch back to idle
        else:
            agent.changeState(Idle)
        # If after shooting and target is not dead, but a higher priority target is nearby, switch targets
        for type in agent.attackorder[:-1]:
            if isinstance(self.victim, type):
                break
            else:
                agents = sorted([(distance(x.getLocation(), agent.getLocation()), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), agent.getLocation(), agent.bullet_range)])
                if len(agents) > 0:
                    #agent.changeState(Attack, agents[0][1])
                    self.victim = agents[0][1]

############################

# BULLETS FOR MINIONS

############################

class StandardBullet(MOBABullet):
	def __init__(self, position, orientation, world, image=BULLET_A, speed=BULLETSPEED_A,
				 damage=BULLETDAMAGE_A, range=BULLETRANGE_A):
		MOBABullet.__init__(self, position, orientation, world, image, speed, damage, range)

class MeleeBullet(MOBABullet):
	def __init__(self, position, orientation, world, image=BULLET_B, speed=BULLETSPEED_B,
				 damage=BULLETDAMAGE_B, range=BULLETRANGE_B):
		MOBABullet.__init__(self, position, orientation, world, image, speed, damage, range)

class AoEBullet(MOBABullet):
	def __init__(self, position, orientation, world, image=BULLET_C, speed=BULLETSPEED_C,
				 damage=BULLETDAMAGE_C, range=BULLETRANGE_C):
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
		pygame.draw.circle(self.world.background, (255, 0, 0), (int(self.getLocation()[0]), int(self.getLocation()[1])), AREAEFFECTRANGE_C, 1)
		team = self.owner.getTeam()
		for thing in self.world.getEnemyNPCs(team) + self.world.getEnemyCastles(team) + self.world.getEnemyBuildings(team):
			if withinRange(self.getLocation(), thing.getLocation(), AREAEFFECTRANGE_C):
				self.hit(thing)

class AoEWave(AoEBullet):
	def __init__(self, position, orientation, world, image=BULLET_D, speed=(0, 0),
				 damage=BULLETDAMAGE_D, range=BULLETRANGE_D):
		AoEBullet.__init__(self, position, orientation, world, image, speed, damage, range)

	def update(self, delta):
		Bullet.update(self, delta)
		self.explode()
		self.world.deleteBullet(self)

	def collision(self, thing):
		Bullet.collision(self, thing)
	
	def explode(self):
		pygame.draw.circle(self.world.background, (255, 0, 0), (int(self.getLocation()[0]), int(self.getLocation()[1])), self.range, 1)
		team = self.owner.getTeam()
		for thing in self.world.getEnemyNPCs(team) + self.world.getEnemyCastles(team) + self.world.getEnemyBuildings(team):
			if withinRange(self.getLocation(), thing.getLocation(), self.range):
				self.hit(thing)


############################

# MINION SUBCLASSES

############################

ATTACKORDER_A = [Building, CastleBase]

class TankMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=ELITE, speed=SPEED_B, viewangle=360, hitpoints=HITPOINTS_B,
                 firerate=FIRERATE_B, bulletclass=MeleeBullet, attackorder = ATTACKORDER_A):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackorder)

ATTACKORDER_B = [TankMinion, BaseMinion, Building, CastleBase]

class ADCMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED_A, viewangle=360, hitpoints=HITPOINTS_A,
                 firerate=FIRERATE_A, bulletclass=StandardBullet, attackorder = ATTACKORDER_B):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackorder)

class AoEMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=JACKAL, speed=SPEED_C, viewangle=360, hitpoints=HITPOINTS_C,
                 firerate=FIRERATE_C, bulletclass=AoEBullet, attackorder = ATTACKORDER_B):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackorder)

class AoEWarrior(BaseMinion):
    def __init__(self, position, orientation, world, image=JACKAL, speed=SPEED_D, viewangle=360, hitpoints=HITPOINTS_D,
                 firerate=FIRERATE_D, bulletclass=AoEWave, attackorder = ATTACKORDER_B):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackorder)