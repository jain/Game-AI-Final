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

'''
This file implements the BaseMinion class and a Finite State Machine for the Minion AI
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
ALIGNMENT_WEIGHT = 1
COHESION_WEIGHT = 3
SEPARATION_WEIGHT = 3
INFLUENCE_PERCENT = 0.33

## MINION A'S CONSTANTS ##
SPEED_A = (5, 5)
HITPOINTS_A = 40
FIRERATE_A = 10
BULLET_A = "sprites/bullet.gif"
BULLETSPEED_A = (20, 20)
BULLETDAMAGE_A = 3
BULLETRANGE_A = 150

## MINION B'S CONSTANTS ##
SPEED_B = (3, 3)
HITPOINTS_B = 120
FIRERATE_B = 20
BULLET_B = "sprites/bullet.gif"
BULLETSPEED_B = (20, 20)
BULLETDAMAGE_B = 5
BULLETRANGE_B = 35

## MINION C'S CONSTANTS ##
SPEED_C = (4, 4)
HITPOINTS_C = 25
FIRERATE_C = 80
BULLET_C = "sprites/bullet2.gif"
BULLETSPEED_C = (15, 15)
BULLETDAMAGE_C = 10
BULLETRANGE_C = 200
AREAEFFECTRANGE_C = 50

## MINION D'S CONSTANTS ##
SPEED_D = (2, 2)
HITPOINTS_D = 100
FIRERATE_D = 50
BULLET_D = "sprites/bullet2.gif"
BULLETDAMAGE_D = 10
BULLETRANGE_D = 50

############################

# BASE MINION CLASS

############################

class BaseMinion(Minion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED, viewangle=360, hitpoints=HITPOINTS,
                 firerate=FIRERATE, bulletclass=SmallBullet, attackOrder = [], moveOrder = []):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.grouping_range = GROUPING_RANGE
        self.states = [Idle, Move, Attack]
        self.world = world
        self.position = position
        self.bullet = bulletclass
        self.bullet_range = bulletclass((0,0),0,None).range
        self.attackOrder = attackOrder
        self.moveOrder = moveOrder
        #self.focusTarget = None

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
            v = numpy.add(v, numpy.multiply(numpy.subtract(ally.getLocation(), self.getLocation()), dropoff))
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
        #v = [m*n*INFLUENCE_PERCENT for m,n in zip(v, self.speed)]
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
                normalizedDirection = numpy.multiply(normalizedDirection, 1-INFLUENCE_PERCENT)
                normalizedDirection = numpy.add(normalizedDirection, self.getInfluenceVector())
                next = [m*n for m,n in zip(normalizedDirection,self.speed)]
                if all(abs(a) < abs(b) for a,b in zip(targetDistance, next)):
                    next = targetDistance
                #normalizedDirection = [x/mag for x in direction]
                #next = [m*n for m,n in zip(normalizedDirection,self.speed)]
                #next = numpy.add(next, self.getInfluenceVector())
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
    
    #def setFocusTarget(self, target):
    #    self.focusTarget = target
    #
    def getFocusTarget(self):
    #    return self.focusTarget
        return self.world.getAllyAI(self.team).getFocusTarget()
    
    def setAttackOrder(self, order):
        self.attackOrder = order
    
    def setMoveOrder(self, order):
        self.moveOrder = order

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
        team = agent.getTeam()
        focusTarget = agent.getFocusTarget()
        
        # Check if we have a focus target, and if so, try to attack or move toward them
        if focusTarget is not None:
            if focusTarget.getTeam() != team and withinRange(focusTarget.getLocation(), pos, agent.bullet_range):
                agent.changeState(Attack, focusTarget)
            else:
                agent.changeState(Move, focusTarget)
        else:
            # Following ATTACK_ORDER listing, look for nearby agents and attack closest, highest priority target
            for type in agent.attackOrder:
                agents = sorted([(distance(x.getLocation(), pos), x) for x in agent.getVisibleType(type) if x.getTeam() != team and withinRange(x.getLocation(), pos, agent.bullet_range)])
                if len(agents) > 0:
                    agent.changeState(Attack, agents[0][1])
                    break
            
            # Following MOVE_ORDER listing, look for nearby agents and attack closest, highest priority target
            for type in agent.moveOrder:
                # Fetch correct list
                alltargets = agent.world.getEnemyNPCs(team) + agent.world.getEnemyBuildings(team) + agent.world.getEnemyCastles(team)
                validtargets = [n for n in alltargets if isinstance(n, type)]
                # If non-empty, find nearest object, set as target, and move towards it
                if len(validtargets) > 0:
                    ordered = sorted([(distance(x.getLocation(), pos), x) for x in validtargets])
                    agent.changeState(Move, ordered[0][1])
                    break
        
        # Else, do nothing
        return None


############################

### Move
###
### Agent is not within range of anything attackable
### Moves toward goal until it reaches something attackable and within range

class Move(State):
    
    def parseArgs(self, args):
        self.target = args[0]
        self.agent.navigateTo(self.target.getLocation())
    
    def execute(self, delta = 0):
        agent = self.agent
        focusTarget = agent.getFocusTarget()
        
        # Check if we have a focus target, and if so, try to attack or move toward them
        if focusTarget is not None:
            if self.target is not focusTarget:
                self.target = focusTarget
            if agent.getMoveTarget() is not self.target.getLocation():
                agent.navigateTo(self.target.getLocation())
            if focusTarget.getTeam() != agent.getTeam() and withinRange(focusTarget.getLocation(), pos, agent.bullet_range):
                agent.changeState(Attack, focusTarget)
        # If we do not have a focus target but our current target does not exist or is on our side, switch to Idle
        elif self.target == None or self.target not in agent.world.getEverything() or agent.getMoveTarget() == None or self.target.getTeam() == agent.getTeam():
            agent.changeState(Idle)
        else:
            # If target's position has changed, update the navigator
            if agent.getMoveTarget() is not self.target.getLocation():
                agent.navigateTo(self.target.getLocation())
            # Following ATTACK_ORDER listing, look for nearby agents and attack closest, highest priority target
            for type in agent.attackOrder:
                agents = sorted([(distance(x.getLocation(), agent.getLocation()), x) for x in agent.getVisibleType(type) if x.getTeam() != agent.getTeam() and withinRange(x.getLocation(), agent.getLocation(), agent.bullet_range)])
                if len(agents) > 0:
                    agent.changeState(Attack, agents[0][1])
                    break

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
        
        # Check if we have a focus target, and if not our current victim, switch to idle for motion or attacking
        if agent.getFocusTarget() is not None and self.victim is not agent.getFocusTarget():
            agent.changeState(Idle)
        
        # Check that victim exists and is not already dead or now out of range
        if self.victim is not None and self.victim in agent.getVisible() and withinRange(agent.getLocation(), self.victim.getLocation(), agent.bullet_range):
            agent.turnToFace(self.victim.getLocation())
            agent.shoot()
        # If target is dead or out of range, switch back to idle
        else:
            agent.changeState(Idle)
        # If after shooting and target is not dead, but a higher priority target is nearby, switch targets
        for type in agent.attackOrder[:-1]:
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

ORDER_A = [Building, CastleBase]

class TankMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=ELITE, speed=SPEED_B, viewangle=360, hitpoints=HITPOINTS_B,
                 firerate=FIRERATE_B, bulletclass=MeleeBullet, attackOrder = ORDER_A, moveOrder = ORDER_A):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackOrder, moveOrder)

ORDER_B = [TankMinion, BaseMinion, Building, CastleBase]
ORDER_C = [BaseMinion, Building, CastleBase]

class ADCMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED_A, viewangle=360, hitpoints=HITPOINTS_A,
                 firerate=FIRERATE_A, bulletclass=StandardBullet, attackOrder = ORDER_B, moveOrder = ORDER_B):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackOrder, moveOrder)

class AoEMinion(BaseMinion):
    def __init__(self, position, orientation, world, image=JACKAL, speed=SPEED_C, viewangle=360, hitpoints=HITPOINTS_C,
                 firerate=FIRERATE_C, bulletclass=AoEBullet, attackOrder = ORDER_B, moveOrder = ORDER_B):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackOrder, moveOrder)

class AoEWarrior(BaseMinion):
    def __init__(self, position, orientation, world, image=JACKAL, speed=SPEED_D, viewangle=360, hitpoints=HITPOINTS_D,
                 firerate=FIRERATE_D, bulletclass=AoEWave, attackOrder = ORDER_B, moveOrder = ORDER_C):
        BaseMinion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass, attackOrder, moveOrder)
