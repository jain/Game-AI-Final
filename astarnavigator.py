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

import sys, pygame, math, numpy, random, time, copy, Queue
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from mycreatepathnetwork import *
from mynavigatorhelpers import *


###############################
### AStarNavigator
###
### Creates a path node network and implements the FloydWarshall all-pairs shortest-path algorithm to create a path to the given destination.
			
class AStarNavigator(NavMeshNavigator):

	def __init__(self):
		NavMeshNavigator.__init__(self)
		

	### Create the pathnode network and pre-compute all shortest paths along the network.
	### self: the navigator object
	### world: the world object
	def createPathNetwork(self, world):
		self.pathnodes, self.pathnetwork, self.navmesh = myCreatePathNetwork(world, self.agent)
		return None
		
	### Finds the shortest path from the source to the destination using A*.
	### self: the navigator object
	### source: the place the agent is starting from (i.e., it's current location)
	### dest: the place the agent is told to go to
	def computePath(self, source, dest):
		### Make sure the next and dist matricies exist
		if self.agent != None and self.world != None: 
			self.source = source
			self.destination = dest
			### Step 1: If the agent has a clear path from the source to dest, then go straight there.
			###   Determine if there are no obstacles between source and destination (hint: cast rays against world.getLines(), check for clearance).
			###   Tell the agent to move to dest
			### Step 2: If there is an obstacle, create the path that will move around the obstacles.
			###   Find the pathnodes closest to source and destination.
			###   Create the path by traversing the self.next matrix until the pathnode closes to the destination is reached
			###   Store the path by calling self.setPath()
			###   Tell the agent to move to the first node in the path (and pop the first node off the path)
			if clearShot(source, dest, self.world.getLines(), self.world.getPoints(), self.agent):
				self.agent.moveToTarget(dest)
			else:
				start = findClosestUnobstructed(source, self.pathnodes, self.world.getLinesWithoutBorders())
				end = findClosestUnobstructed(dest, self.pathnodes, self.world.getLinesWithoutBorders())
				if start != None and end != None:
					#print len(self.pathnetwork)
					newnetwork = unobstructedNetwork(self.pathnetwork, self.world.getGates())
					#print len(newnetwork)
					closedlist = []
					path, closedlist = astar(start, end, newnetwork)
					if path is not None and len(path) > 0:
						path = shortcutPath(source, dest, path, self.world, self.agent)
						self.setPath(path)
						if self.path is not None and len(self.path) > 0:
							first = self.path.pop(0)
							self.agent.moveToTarget(first)
		return None
		
	### Called when the agent gets to a node in the path.
	### self: the navigator object
	def checkpoint(self):
		myCheckpoint(self)
		return None

	### This function gets called by the agent to figure out if some shortcutes can be taken when traversing the path.
	### This function should update the path and return True if the path was updated.
	def smooth(self):
		return mySmooth(self)

	def update(self, delta):
		myUpdate(self, delta)


def unobstructedNetwork(network, worldLines):
	newnetwork = []
	for l in network:
		hit = rayTraceWorld(l[0], l[1], worldLines)
		if hit == None:
			newnetwork.append(l)
	return newnetwork




def astar(init, goal, network):
	path = []
	open = []
	closed = []
	### YOUR CODE GOES BELOW HERE ###
	
	# Initialize queues
	q_open = Queue.PriorityQueue()
	q_closed = Queue.PriorityQueue()
	gs = []
	
	def getG(node):
		return [g for (n, g) in gs if n == node][0]
	# adds a G to the table; returns true if there was an update/replacement
	def addG(node, g):
		xs = [(n, ng) for (n, ng) in gs if n == node]
		if len(xs) > 0:
			if g < xs[0][1]:
				gs.remove(xs[0])
				gs.append((node, g))
		else:
			gs.append((node, g))
	
	# Method which pops next node in queue and expands it fully to find path to goal
	def processNextNode():
		# Get next node from open queue and remove it from other list
		(priority, current, parent) = q_open.get()
		open.remove((priority, current, parent))
		# If current node was explored previously, skip it
		if current in closed:
			return False
		# Add the current node to the closed list
		q_closed.put((priority, current, parent))
		# If current node is goal, return signal to trigger path generation
		if current == goal:
			return True
		# Find all neighbors of the current node which have not been fully explored
		nodesAB = [a for (a, b) in network if a not in closed and b == current]
		nodesBA = [a for (b, a) in network if a not in closed and b == current]
		nodes = list(set(nodesAB) | set(nodesBA))
		# For each node in this list...
		for n in nodes:
			# Add its g priority to the table
			g = getG(current) + distance(current, n)
			addG(n, g)
			# Find its total priority
			p = getG(n) + distance(n, goal)
			# Check if the node is already in the open list
			old = sorted([(op, on) for (op, on, _) in open if on == n])
			# If it's in the open list and the new priority is better, add it
			if len(old) > 0:
				if p < old[0][0]:
					q_open.put((p, n, current))
					open.append((p, n, current))
			# If node does not exist in open, add it
			else:
				q_open.put((p, n, current))
				open.append((p, n, current))
		# Add node to closed list
		closed.append(current)
		return False
	
	# Generate the path based on the final closed node queue
	def generatePath():
		index = []
		nodes = []
		# Empty closed queue into index for lookup
		while q_closed.empty() == False:
			(_, node, parent) = q_closed.get()
			index.append((node, parent))
		# Starting at goal, begin backwards traversal for fully constructed path
		next = goal
		while next is not None:
			[(node, next)] = [(n, p) for (n, p) in index if n == next]
			nodes.append(node)
		return nodes[::-1]
	
	# Insert initial node into open queue and lists
	q_open.put((0, init, None))
	open.append((0, init, None))
	addG(init, 0)
	
	# Continuously process each lowest priority node in the open queue until either goal is found or queue is empty
	isGoal = False
	while (isGoal or q_open.empty()) == False:
		isGoal = processNextNode()
	
	# If goal was found, generate the path from the closed node queue
	# Else, no goal was found, return an empty path
	path = generatePath() if isGoal else None
	
	### YOUR CODE GOES ABOVE HERE ###
	return path, closed
	
	


def myUpdate(nav, delta):
	### YOUR CODE GOES BELOW HERE ###
	
	agent = nav.agent
	dest = nav.getDestination()
	lines = nav.world.getLinesWithoutBorders()
	points = nav.world.getPoints()
	
	#	# If path to the next checkpoint (or goal) is not clear, stop
	if dest is not None and clearShot(agent.getLocation(), agent.getMoveTarget(), lines, points, agent) == False:
		agent.navigateTo(dest)
		if nav.getPath() == None:
			agent.stop()
	
	### YOUR CODE GOES ABOVE HERE ###
	return None



def myCheckpoint(nav):
	### YOUR CODE GOES BELOW HERE ###
	
	# Assumes there is always a desination during a checkpoint, so no check that destination is valid
	agent = nav.agent
	dest = nav.getDestination()
	lines = nav.world.getLinesWithoutBorders()
	points = nav.world.getPoints()
	
	# Build path to trace
	path = [agent.getLocation(), agent.getMoveTarget()]
	path.extend(nav.getPath())
	path.append(dest)
	
	# Check every edge along the path for any obstructions
	for i in xrange(len(path) - 1):
		# If path is blocked, find new route (recalculate)
		if clearShot(path[i], path[i + 1], lines, points, agent) == False:
			# Stop agent
			agent.stop()
			# Form new path
			agent.navigateTo(nav.getDestination())
			# If path to go exists, start moving again
			if nav.getPath() is not None:
				agent.start()
	
	### YOUR CODE GOES ABOVE HERE ###
	return None


### Returns true if the agent can get from p1 to p2 directly without running into an obstacle.
### p1: the current location of the agent
### p2: the destination of the agent
### worldLines: all the lines in the world
### agent: the Agent object
def clearShot(p1, p2, worldLines, worldPoints, agent):
	### YOUR CODE GOES BELOW HERE ###
	
	def minDistance(point):
		best = INFINITY
		for line in worldLines:
			current = minimumDistance(line, point)
			if current < best:
				best = current
		return best
	
	# Insurance check to avoid divide by zero error
	if distance(p1, p2) < EPSILON:
		return True
	# Fetch agent's max radius
	radius = agent.getMaxRadius()
	# Find the deltas in x and y, and scale them based on length of agent's max radius
	(dx, dy) = numpy.multiply(numpy.subtract(p2, p1), radius / distance(p1, p2))
	# Swap x and y and flip sign of one for perpendicular translation vector
	p = (dy, -dx)
	# Check edges of agent line of travel for collisions; add line if no collision
	if rayTraceWorld(numpy.add(p1, p), numpy.add(p2, p), worldLines) == None:
		if rayTraceWorld(numpy.subtract(p1, p), numpy.subtract(p2, p), worldLines) == None:
			if minDistance(p1) > radius and minDistance(p2) > radius:
				return True
	
	### YOUR CODE GOES ABOVE HERE ###
	return False

