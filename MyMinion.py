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

class MyMinion(Minion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED, viewangle=360, hitpoints=HITPOINTS,
                 firerate=FIRERATE, bulletclass=SmallBullet):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.states = [Idle, Move, AttackMinionHero, AttackBuildingCastle]
        self.world = world
        self.position = position
        self.bullet = bulletclass
        self.bullet_range = bulletclass((0,0),0,None).range

    ### Add your states to self.states (but don't remove Idle)
    ### YOUR CODE GOES BELOW HERE ###

    ### YOUR CODE GOES ABOVE HERE ###

    def start(self):
        Minion.start(self)
        self.changeState(Idle)


############################
### Idle
###
### This is the default state of MyMinion. The main purpose of the Idle state is to figure out what state to change to and do that immediately.

class Idle(State):
    # Moving = True
    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()
        self.Moving = True

    def execute(self, delta=0):
        '''
        State.execute(self, delta)
        ### YOUR CODE GOES BELOW HERE ###
        print "Team: ",self.agent.getTeam()
        print "Get visible: ", self.agent.getVisibleType(Hero)
        heroes = self.agent.getVisibleType(Hero)
        for h in heroes:
            print "h team: ", h.getTeam()
        print "Get possible dest: ", self.agent.getPossibleDestinations()
        print "world NPCs: ", self.agent.world.getNPCs()
        #print "range: ",self.agent.bulletclass.range
        '''
        #print "IDLE STATE"
        myTeam = self.agent.getTeam()
        buildings = self.agent.world.getEnemyBuildings(myTeam)
        myCastle = self.agent.world.getCastleForTeam(myTeam)
        #print "NO OF MINIONS: ", myBase.numSpawned
        if buildings:
            nearBuilding, nearBuildDist = getNearest(self.agent, buildings)
            self.agent.changeState(Move, nearBuilding)
        else:
            castles = self.agent.world.getEnemyCastles(myTeam)
            if castles:
                nearCastle, nearCastleDist = getNearest(self.agent, castles)
                self.agent.changeState(Move, nearCastle)
        '''
        if self.agent.isMoving() == False:
            self.timest = delta
            self.Moving = False
        if self.Moving == False and self.agent.isMoving() == False and delta > self.timest + 7:
            self.agent.changeState(Idle)
        '''
        ### YOUR CODE GOES ABOVE HERE ###
        return None


##############################
### Taunt
###
### This is a state given as an example of how to pass arbitrary parameters into a State.
### To taunt someome, Agent.changeState(Taunt, enemyagent)

class Taunt(State):
    def parseArgs(self, args):
        self.victim = args[0]

    def execute(self, delta=0):
        if self.victim is not None:
            print "Hey " + str(self.victim) + ", I don't like you!"
        self.agent.changeState(Idle)


##############################
### YOUR STATES GO HERE:



class Move(State):
    def parseArgs(self, args):
        self.target = args[0]

    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.navigateTo(self.target.getLocation())

    def execute(self, delta=0):

        #print "MOVE STATE"
        tower = 0
        if distance(self.agent.getLocation(), self.target.getLocation()) <= self.agent.bullet_range:
            self.agent.changeState(AttackBuildingCastle, self.target)
            tower = tower + 1

        count = 0
        # if delta % 3 == 0:
        myTeam = self.agent.getTeam()
        minions = self.agent.getVisibleType(Minion)
        for m in minions:
            if m.getTeam() != myTeam:
                if distance(self.agent.getLocation(), m.getLocation()) <= self.agent.bullet_range and tower == 0 and distance(
                        self.agent.getLocation(), self.target.getLocation()) > TOWERBULLETRANGE:
                    self.agent.changeState(AttackMinionHero, m)
                    count = count + 1
                    break
        '''
        if count == 0:
            heroes = self.agent.getVisibleType(Hero)
            for h in heroes:
                if h.getTeam() != myTeam:
                    if distance(self.agent.getLocation(),
                                h.getLocation()) <= SMALLBULLETRANGE and tower == 0 and distance(
                            self.agent.getLocation(), self.target.getLocation()) > TOWERBULLETRANGE:
                        self.agent.changeState(AttackMinionHero, h)
                        count = count + 1
                        break'''

        if delta % 10 == 0:
            self.agent.navigateTo(self.target.getLocation())
            # if count == 0 and tower == 0:
            #	self.agent.changeState(Idle)
            # print "Dest: ",self.agent.getPossibleDestinations()

            # def exit(self):
            #	self.agent.stopMoving()


class AttackMinionHero(State):
    def parseArgs(self, args):
        self.target = args[0]

    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()

    # self.agent.navigateTo(self.target.getLocation())

    def execute(self, delta=0):
        #print "ATTACK MINION STATE"
        self.agent.turnToFace(self.target.getLocation())
        self.agent.shoot()
        if delta % 4 == 0:
            if self.target.getHitpoints() > 0 and distance(self.agent.getLocation(),
                                                           self.target.getLocation()) <= self.agent.bullet_range:
                self.agent.turnToFace(self.target.getLocation())
                self.agent.shoot()
            else:
                self.agent.changeState(Idle)


class AttackBuildingCastle(State):
    def parseArgs(self, args):
        self.target = args[0]

    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()

    def execute(self, delta=0):
        #print "ATTACK BASE TOWER STATE"
        self.agent.turnToFace(self.target.getLocation())
        self.agent.shoot()
        if delta % 4 == 0:
            if self.target.getHitpoints() > 0 and distance(self.agent.getLocation(),
                                                           self.target.getLocation()) <= self.agent.bullet_range:
                self.agent.turnToFace(self.target.getLocation())
                self.agent.shoot()
            else:
                self.agent.changeState(Idle)


def getNearest(item, itemlist):
    itemloc = item.getLocation()
    mindist = distance(itemloc, itemlist[0].getLocation())
    dest = itemlist[0]
    for i in itemlist:
        if distance(itemloc, i.getLocation()) < mindist:
            mindist = distance(itemloc, i.getLocation())
            dest = i
    return dest, mindist


def checkptCollision(p1, p2, world, agent):
    radius = agent.getMaxRadius() + 1.5
    # print "Max radius: ", radius
    obstacleList = world.getObstacles()
    worlddim = world.getDimensions()
    # print worlddim
    worldx, worldy = worlddim
    worldlines = [((0, 0), (worldx, 0)), ((worldx, 0), (worldx, worldy)), ((worldx, worldy), (0, worldy)),
                  ((0, worldy), (0, 0))]
    worldpoints = [(0, 0), (worldx, 0), (worldx, worldy), (0, worldy)]

    # print "points"
    # print p1, p2
    x1, y1 = p1
    x2, y2 = p2
    dx = float(x1 - x2)
    dy = float(y1 - y2)
    # print "dx = ",dx
    # print "dy = ", dy
    dist = 1.0
    dist = float(sqrt(dx * dx + dy * dy))
    # print dist
    dx = dx / dist
    dy = dy / dist
    x3 = x1 + radius * dy
    y3 = y1 - radius * dx
    x4 = x1 - radius * dy
    y4 = y1 + radius * dx

    x5 = x2 + radius * dy
    y5 = y2 - radius * dx
    x6 = x2 - radius * dy
    y6 = y2 + radius * dx
    # print "3,4",(x3,y3),(x4,y4)
    # print "5,6", (x5,y5),(x6, y6)
    collision = False
    for obstacle in obstacleList:
        if rayTraceWorld((x3, y3), (x5, y5), obstacle.getLines()) is not None or rayTraceWorld((x4, y4), (x6, y6),
                                                                                               obstacle.getLines()) is not None or rayTraceWorld(
                p1, p2, obstacle.getLines()) is not None or rayTraceWorld((x3, y3), (x5, y5),
                                                                          world.getLinesWithoutBorders()) is not None or rayTraceWorld(
                (x4, y4), (x6, y6), world.getLinesWithoutBorders()) is not None or rayTraceWorld(p1, p2,
                                                                                                 world.getLinesWithoutBorders()) is not None:
            collision = True
            # print "collision"
    polypoints = [(x3, y3), (x5, y5), (x6, y6), (x4, y4)]
    for obstacle in obstacleList:
        for point in obstacle.getPoints():
            if point_inside_polygon(point, polypoints) == True:
                collision = True
    for obstacle in obstacleList:
        for point in obstacle.getPoints():
            x, y = point
            if ((x - x1) * (x - x1)) + ((y - y1) * (y - y1)) < radius * radius:
                collision = True
            if ((x - x2) * (x - x2)) + ((y - y2) * (y - y2)) < radius * radius:
                collision = True
    # if collision == False:
    #	drawPolygon(polypoints,world.debug, (255,0,255), 2, False)
    return collision

def point_inside_polygon(pt,poly):
	x, y = pt
	n = len(poly)
	inside =False

	p1x,p1y = poly[0]
	for i in range(n+1):
		p2x,p2y = poly[i % n]
		if y > min(p1y,p2y):
			if y <= max(p1y,p2y):
				if x <= max(p1x,p2x):
					if p1y != p2y:
						xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
					if p1x == p2x or x <= xinters:
						inside = not inside
		p1x,p1y = p2x,p2y

	return inside
