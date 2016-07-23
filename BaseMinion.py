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

GROUPING_RANGE = 250
ALIGNMENT_WEIGHT = 0.25
COHESION_WEIGHT = 1
SEPARATION_WEIGHT = 3

class BaseMinion(Minion):
    def __init__(self, position, orientation, world, image=NPC, speed=SPEED, viewangle=360, hitpoints=HITPOINTS,
                 firerate=FIRERATE, bulletclass=SmallBullet):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.grouping_range = GROUPING_RANGE
    
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
        if vectorMagnitude(v) != 0:
            v = numpy.divide(v, vectorMagnitude(v))
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
                direction = numpy.add(normalizedDirection, self.getInfluenceVector())
                normalizedDirection = [x/vectorMagnitude(direction) for x in direction]
                targetDistance = numpy.subtract(self.moveTarget, self.getLocation())
                next = [m*n for m,n in zip(normalizedDirection,self.speed)]
                if all(abs(a) < abs(b) for a,b in zip(targetDistance, next)):
                    next = targetDistance
                #normalizedDirection = [x/mag for x in direction]
                #next = [m*n for m,n in zip(normalizedDirection,self.speed)]
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