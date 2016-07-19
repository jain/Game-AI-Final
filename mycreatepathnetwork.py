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

import sys, pygame, math, numpy, random, time, copy, operator
from pygame.locals import *

from constants import *
from utils import *
from core import *

# Creates a pathnode network that connects the midpoints of each navmesh together
def myCreatePathNetwork(world, agent = None):
	nodes = []
	edges = []
	polys = []
	### YOUR CODE GOES BELOW HERE ###
	
	# Get list of all points in the world
	points = world.getPoints()
	# Get list of all obstacle lines minus the world borders
	lines = world.getLinesWithoutBorders()
	# Get all obstacles
	obstacles = world.getObstacles()
	# Get agent's max radius
	#if Agent != None:
	#	radius = agent.getMaxRadius()
	#else:
	radius = world.getAgent().getMaxRadius()
	
	### SUPPLEMENTARY FUNCTIONS ###
	
	# Returns list of lines of polygon
	def getPolygonLines(polygon):
		list = []
		for i in xrange(len(polygon)):
			list.append((polygon[i], polygon[(i + 1)%len(polygon)]))
		return list
	
	# Checks if a polygon overlaps with any other polygon from a list of polygons
	def isPolygonValid(polygon, polys):
		polygonLines = getPolygonLines(polygon)
		# For each existing polygon, check for overlap
		for poly in polys:
			# Get list of all lines from poly that are not shared with tested polygon
			polyLines = [(a, b) for (a, b) in getPolygonLines(poly) if (a, b) not in polygonLines and (b, a) not in polygonLines]
			# Check for intersections with non-shared edges, invalid if any overlap
			for i in xrange(len(polygon)):
				if rayTraceWorldNoEndPoints(polygon[i], polygon[(i + 1)%len(polygon)], polyLines) != None:
					return False
			# Check if new polygon is within existing poly
			polygon_unique = [x for x in polygon if x not in poly]
			for x in polygon_unique:
				if pointInsidePolygonPoints(x, poly):
					return False
			# Check if existing poly is within new polygon
			poly_unique = [x for x in poly if x not in polygon]
			for x in poly_unique:
				if pointInsidePolygonPoints(x, polygon):
					return False
			# Check if existing poly is same as new polygon (extra step for debugging duplicates)
			if sorted(polygon) == sorted(poly):
				return False
		return True
	
	# Takes two lists of polygon points and returns an ordering of the merged polygon
	def mergePolygons(polygon1, polygon2):
		# Get shared vertices p1 and p2
		[p1, p2] = [p for p in polygon1 if p in polygon2]
		
		# Check indices of p1 and p2, swap labels if p1 and p2 are at opposite ends of sequence
		if polygon1.index(p1) + len(polygon1) - 1 == polygon1.index(p2):
			temp = p1
			p1 = p2
			p2 = temp
		
		# Rearrange points in polygon1 such that order is (p1, p2, ...)
		poly1 = polygon1[polygon1.index(p1):] + polygon1[:polygon1.index(p1)]
		
		# If p1 precedes p2 in polygon2 and are not at opposite ends of sequence, reverse polygon2
		if polygon2.index(p1) < polygon2.index(p2):
			if polygon2.index(p1) + len(polygon2) - 1 != polygon2.index(p2):
				polygon2.reverse()
		
		# Rearrange points in polygon2 such that order is (p2, p1, ...)
		poly2 = polygon2[polygon2.index(p2):] + polygon2[:polygon2.index(p2)]
		
		return poly1[1:] + poly2[1:]
	
	# Returns center of polygon
	def getPolygonCenter(polygon):
		(a, b) = (0, 0)
		for point in polygon:
			(a, b) = numpy.add((a, b), point)
		return numpy.divide((a, b), len(poly))
	
	### COMPUTATION OF POLYGONS ###
	
	# First sweep to find all point combinations which are not obstructed
	pairs = []
	for p in points:
		for q in points[points.index(p) + 1:]:
			# For each unique pair, determine if a line between them is obstructed
			if rayTraceWorldNoEndPoints(p, q, lines) == None:
				# Next check that their midpoint is not inside of an obstacle
				valid = True
				midpoint = ((p[0] + q[0])/2, (p[1] + q[1])/2)
				for obstacle in obstacles:
					obs_points = obstacle.getPoints()
					if pointInsidePolygonPoints(midpoint, obs_points):
						valid = False
						break
				# If not inside obstacle, valid pair for polygon creation
				if valid:
					pairs.append((p, q))
	
	# First sweep does not include obstacle edges, so add those to pairs list
	pairs.extend(lines)
	
	# Find lengths of lines, sort by shortest distances
	dist_pairs = sorted([(ln, distance(ln[0], ln[1])) for ln in pairs], key=lambda x: x[1])
	
	# Go through pairs from shortest distance to longest
	# Visited keeps track of all lines/edges we have completely exhausted
	visited = []
	for ((p, q), _) in dist_pairs:
		# Pre-emptively mark current pair as fully exhausted
		visited.append((p, q))
		# Narrow list to only those unobstructed lines we have not fully exhausted
		selection = [pair for (pair, _) in dist_pairs if pair not in visited]
		# Refine list to only those points that neighbor both p and q
		select_p = [a for (a, _) in selection if (a, p) in selection] + [a for (_, a) in selection if (p, a) in selection]
		select_q = [a for (a, _) in selection if (a, q) in selection] + [a for (_, a) in selection if (q, a) in selection]
		select_both = list(set(select_p) & set(select_q))
		
		## Sort selection by distance to p
		select = [x for (x, _) in sorted([(y, distance(p, y)) for y in select_both], key=lambda y: y[1])]
		
		# Go through all points
		for r in select:
			polygon = [p, q, r]
			if isPolygonValid(polygon, polys):
				polys.append(polygon)
	
	# Remove any and all triangular polygons formed that are identical to existing obstacles
	for obstacle in obstacles:
		shape = sorted(obstacle.getPoints())
		for poly in polys:
			if sorted(poly) == shape:
				polys.remove(poly)
				break
	
	# Move through list of polygons, merge as many polygons into larger, convex shapes as possible
	def mergePass():
		i = 0
		j = len(polys)
		updated = False
		while i < j:
			p1 = polys[i]
			selection = polys[i + 1:]
			for p2 in selection:
				if polygonsAdjacent(p1, p2):
					merged = mergePolygons(p1, p2)
					if isConvex(merged):
						polys.remove(p1)
						polys.remove(p2)
						polys.insert(i, merged)
						p1 = merged
						updated = True
						j = j - 1
			i = i + 1
		return updated
	
	# Makes passes until no more larger convex shapes can be made
	while True:
		updated = mergePass()
		if updated == False:
			break
	
	### GET NODES ###
	
	# Checks if a point is too close to any of the obstacles in the environment
	def isTooClose(point, lines, threshold):
		for line in lines:
			if minimumDistance(line, point) <= threshold:
				return True
		return False
	
	def isClear(a, b):
		# Find the deltas in x and y, and scale them based on length of agent's max radius
		(dx, dy) = numpy.multiply(numpy.subtract(b, a), radius / distance(a, b))
		# Swap x and y and flip sign of one for perpendicular translation vector
		p = (dy, -dx)
		# Check edges of agent line of travel for collisions; add line if no collision
		if rayTraceWorld(numpy.add(a, p), numpy.add(b, p), lines) == None:
			if rayTraceWorld(numpy.subtract(a, p), numpy.subtract(b, p), lines) == None:
				return True
		return False
	
	polynodes = []
	# From all polygons, find centers and add as nodes
	for poly in polys:
		# Find center of polygon
		(a, b) = getPolygonCenter(poly)
		# If center of polygon is far enough from any obstacle...
		if isTooClose((a, b), lines, radius) == False:
			# Add to list of nodes, log as center of its polygon in polynodes
			nodes.append((a, b))
			polynodes.append((poly, (a, b)))

	# Check now for portals, find their midpoint nodes and add edges as able
	# Check each poly against each other
	for p1 in polys:
		for p2 in polys[polys.index(p1) + 1:]:
			# If polygons are adjacent, find adjacent edge
			if polygonsAdjacent(p1, p2):
				portal = [x for x in p1 if x in p2]
				# Check if portal is wide enough for agent to pass through
				if distance(portal[0], portal[1]) > 2*radius:
					(a, b) = numpy.divide(numpy.add(portal[0], portal[1]), 2)
					nodes.append((a, b))
					centers = [c for (p, c) in polynodes if p in [p1, p2]]
					for center in centers:
						if isClear((a, b), center):
							edges.append(((a, b), center))
	
	### YOUR CODE GOES ABOVE HERE ###
	return nodes, edges, polys

	
