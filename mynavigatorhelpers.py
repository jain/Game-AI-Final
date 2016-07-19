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

# Copied from apspnavigator.py for use in shortcut code
def clearShot(p1, p2, worldLines, worldPoints, agent):
		### YOUR CODE GOES BELOW HERE ###
		
		if distance(p1, p2) == 0:
			return True
		# Find the deltas in x and y, and scale them based on length of agent's max radius
		(dx, dy) = numpy.multiply(numpy.subtract(p2, p1), agent.getMaxRadius() / distance(p1, p2))
		# Swap x and y and flip sign of one for perpendicular translation vector
		p = (dy, -dx)
		# Check edges of agent line of travel for collisions; add line if no collision
		if rayTraceWorld(numpy.add(p1, p), numpy.add(p2, p), worldLines) == None:
			if rayTraceWorld(numpy.subtract(p1, p), numpy.subtract(p2, p), worldLines) == None:
				return True
		
		### YOUR CODE GOES ABOVE HERE ###
		return False

### This function optimizes the given path and returns a new path
### source: the current position of the agent
### dest: the desired destination of the agent
### path: the path previously computed by the Floyd-Warshall algorithm
### world: pointer to the world
def shortcutPath(source, dest, path, world, agent):
	### YOUR CODE GOES BELOW HERE ###

	lines = world.getLinesWithoutBorders()
	points = world.getPoints()
	
	newpath = []
	# Set initial seek-from point
	a = source
	# Check each node from seek-from point as we move along, skipping immediate successor
	for b in path:
		# Look for first node NOT reachable from a
		if clearShot(a, b, lines, points, agent) == False:
			# Append the previous node to the new path, set it as new seek-from point
			a = path[path.index(b) - 1]
			newpath.append(a)
	
	# Check the last seek-from point against the destination, add last path node if needed
	if clearShot(a, dest, lines, points, agent) == False:
		newpath.append(path[-1])
	
	path = newpath
	
	### YOUR CODE GOES BELOW HERE ###
	return path



### This function changes the move target of the agent if there is an opportunity to walk a shorter path.
### This function should call nav.agent.moveToTarget() if an opportunity exists and may also need to modify nav.path.
### nav: the navigator object
### This function returns True if the moveTarget and/or path is modified and False otherwise
def mySmooth(nav):
	### YOUR CODE GOES BELOW HERE ###
	
	# Copied from nearestgatherer.py
	def sortTargets(location, targets):
		# Get the closest
		start = None
		dist = INFINITY
		for t in targets:
			d = distance(location, t) 
			if d < dist:
				start = t
				dist = d
		# ASSERT: start has the closest node
		remaining = [] + targets
		sorted = [start]
		remaining.remove(start)
		current = start
		while len(remaining) > 0:
			closest = None
			dist = INFINITY
			for t in remaining:
				d = distance(current, t)
				if d < dist:
					closest = t
					dist = d
			sorted.append(closest)
			remaining.remove(closest)
			current = closest
		return sorted
	
	agent = nav.agent
	pos = agent.position
	dest = nav.destination
	lines = nav.world.getLinesWithoutBorders()
	points = nav.world.getPoints()
	if isinstance(agent, Gatherer):
		targets = agent.targets
	else:
		targets = []
	
	# Check if there is a closer node to travel to first
	if targets != []:
		sorted = sortTargets(pos, targets)
		if dest != sorted[0]:
			agent.targets = sorted
			nav.computePath(pos, sorted[0])
			return True
	
	# First check if destination is within view; if so, move toward it
	if dest is not None:
		if clearShot(pos, dest, lines, points, agent):
			agent.moveToTarget(dest)
			return True
		
		# Next check points in path in reverse order to see if we can skip to one closer to destination
		if nav.path is not None:
			for point in nav.path[::-1]:
				if clearShot(pos, point, lines, points, agent):
					agent.moveToTarget(point)
					return True
	
	### YOUR CODE GOES ABOVE HERE ###
	return False



