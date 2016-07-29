################################
#                              #
# AI CLASS AND SUBCLASSES FILE #
#                              #
################################

from constants import *
from utils import *
import math
from astarnavigator import AStarNavigator
from moba2 import SmallBullet, BigBullet, BaseBullet
from Castle import *
from Minions import *
from RLCsv import RLCsv

AIBUILDRATE = 10

################################

# BASIC AI MODEL

################################

class BaseAI():
	def __init__(self, world, team=None, buildRate=AIBUILDRATE):
		self.world = world
		self.team = team
		self.buildTimer = 0
		self.buildRate = buildRate
		self.buildings = [FACTORY1, FACTORY2, FACTORY3, TOWER, MINE, RESOURCE]
		self.costs = [300, 500, 700, 500, 600, 700]
		self.factories = [FACTORY1, FACTORY2, FACTORY3]
		self.minionTypes = [ADCMinion, TankMinion, AoEMinion]
		#self.lastBuild = None
		self.behaviorTree = None
		self.focusTarget = None
		self.rl = RLCsv()
	
	def getTeam(self):
		return self.team

	def update(self, delta):
		# Check if base is dead; if so, victory goes to opponent
		if len(self.world.getCastleForTeam(self.team)) == 0:
			print "Team", 3 - self.team, "wins!"
			self.world.gameover = True
		
		alltargets = self.world.getEverything()
		if self.focusTarget is not None and self.focusTarget not in alltargets:
			self.focusTarget = None
		self.buildTimer += 1
		# Check if we should build
		if self.buildTimer >= self.buildRate:
			self.buildTimer = 0
			myKingdom = self.world.getCastlesAndBuildingsForTeam(self.team)
			
			# If we have a behaviorTree set, base our AI on the behavior tree; otherwise, use reinforcement learning
			if self.behaviorTree is not None:
				self.behaviorTree.update()
				basetype = self.behaviorTree.basetype
			else:
				myBuildings = self.world.getBuildingsForTeam(self.team)
				enemyBuildings = self.world.getEnemyBuildings(self.team)
				basetype = self.rl.query(myBuildings, enemyBuildings, self.world.gold[self.team - 1], self.world.gold[1 - (self.team - 1)])
			
			# Terminate early if the basetype is none or if we do not have the gold to build our next structure
			if basetype == None:
				return None
			if self.world.gold[self.team - 1] < self.costs[basetype]:
				return None
			
			# Find a location for the build
			for basept in [base.getLocation() for base in myKingdom]:
				buildpt = self.findPoint(basept, BUILDRADIUS)
				if basetype >= 0 and basetype <=2:
					c3 = Spawner(self.factories[basetype], buildpt, self.world, self.team, self.minionTypes[basetype])
				elif basetype == 3:
					c3 = Defense(TOWER, buildpt, self.world, self.team)
				elif basetype == 4:
					c3 = GoldMiner(MINE, buildpt, self.world, self.team)
				elif basetype == 5:
					c3 = AttackBooster(RESOURCE, buildpt, self.world, self.team)
				
				# If build point is not valid, jump to next loop
				if not self.isValidBuildLocation(c3, myKingdom):
					continue
				
				self.world.gold[self.team - 1] -= self.costs[basetype]
				nav = AStarNavigator()
				nav.agent = self.world.agent
				nav.setWorld(self.world)
				c3.setNavigator(nav)
				self.world.addBuilding(c3)
				if self.behaviorTree is not None:
					self.behaviorTree.basetype = None
				break
		return None
	
	# Finds a point within a given radius of a central point and within the realm of the team field
	def findPoint(self, basept, radius):
		wx, wy = self.world.getDimensions()
		# Set search boundaries based on which side/team we are on
		if self.team == 1:
			boundarypoints = [(0, 0), (wx*PERCENTFIELD, 0), (wx*PERCENTFIELD, wy), (0, wy)]
		else:
			boundarypoints = [(wx*(1 - PERCENTFIELD), 0), (wx, 0), (wx, wy), (wx*(1 - PERCENTFIELD), wy)]
		boundarylines = [(boundarypoints[x%4], boundarypoints[(x+1)%4]) for x in xrange(4)]
		count = 0
		# Repeat generation of points until we find a valid one to return
		while True:
			x = basept[0] + random.random()*2*radius - radius
			y = basept[1] + random.random()*2*radius - radius
			if distance(basept, (x, y)) < radius:
				dist = [minimumDistance(line, (x, y)) for line in boundarylines]
				if min(dist) >= OFFSET and pointInsidePolygonPoints((x,y), boundarypoints):
					return (x,y)
	
	def isValidBuildLocation(self, newbuild, kingdom):
		newlines = newbuild.getLines()
		for building in kingdom:
			oldlines = building.getLines()
			for line in newlines:
				if rayTraceWorld(line[0], line[1], oldlines) is not None or pointInsidePolygonLines(line[0], oldlines):
					return False
			for line in oldlines:
				if pointInsidePolygonLines(line[0], newlines):
					return False
		return True
	
	def doKeyDown(self, key):
		return None
	
	def getFocusTarget(self):
		return self.focusTarget


################################

# HUMAN "AI" MODULE

################################

class Human(BaseAI):

	def __init__(self, world, team=None):
		BaseAI.__init__(self, world, team)
	
	def update(self, delta):
		# Check if base is dead; if so, victory goes to opponent
		if len(self.world.getCastleForTeam(self.team)) == 0:
			print "Team", 3 - self.team, "wins!"
			self.world.gameover = True
		
		alltargets = self.world.getCastlesAndBuildings() + self.world.getNPCsForTeam(self.team) + self.world.getEnemyNPCs(self.team)
		if self.focusTarget is not None and self.focusTarget not in alltargets:
			self.focusTarget = None
	
	def doKeyDown(self, key):
		#if key == 32: #space
		#	self.agent.shoot()
		#elif key == 100: #d
		#	print "distance traveled", self.agent.distanceTraveled
		
		# KEY BINDINGS:
		#	W (119) - ADCMinion Spawner
		#	E (101) - TankMinion Spawner
		#	R (114) - AoEWarrior Spawner
		#	S (115) - Defense
		#	D (100) - Gold Miner
		#	F (102) - Attack Booster
		#	Q (113) - All Agents Return to Base
		#	A (097) - Cancel retreat
		
		if key in [119, 101, 114, 115, 100, 102]:
			loc = self.world.agent.getLocation()
			offs = OFFSET
			wx, wy = self.world.getDimensions()
			if not between(loc[0], OFFSET, wx*PERCENTFIELD - OFFSET) or not between(loc[1], OFFSET, wy - OFFSET):
				print 'U CANT BUILD HERE'
				return None
			#poly = [(loc[0]-offs, loc[1]-offs),(loc[0]+offs, loc[1]-offs),(loc[0]+offs, loc[1]+offs),(loc[0]-offs, loc[1]+offs)]
			if key==119:
				c3 = Spawner(FACTORY1, loc, self.world, self.team, ADCMinion)
				cost = self.costs[0]
			elif key==101:
				c3 = Spawner(FACTORY2, loc, self.world, self.team, TankMinion)
				cost = self.costs[1]
			elif key==114:
				c3 = Spawner(FACTORY3, loc, self.world, self.team, AoEWarrior)
				cost = self.costs[2]
			elif key==115:
				c3 = Defense(TOWER, loc, self.world, self.team)
				cost = self.costs[3]
			elif key==100:
				c3 = GoldMiner(MINE, loc, self.world, self.team)
				cost = self.costs[4]
			elif key==102:
				c3 = AttackBooster(RESOURCE, loc, self.world, self.team)
				cost = self.costs[5]
			if cost > self.world.gold[self.team - 1]:
				print 'NOT ENOUGH GOLD'
				return None
			
			if not self.isValidBuildLocation(c3, self.world.getCastlesAndBuildingsForTeam(self.team)):
				print 'U CANT BUILD HERE'
				return None
			
			self.world.gold[self.team - 1] -= cost
			nav = AStarNavigator()
			nav.agent = self.world.agent
			nav.setWorld(self.world)
			c3.setNavigator(nav)
			self.world.addBuilding(c3)
			
		elif key==113:
			castles = self.world.getCastleForTeam(self.team)
			if len(castles) > 0:
				self.focusTarget = castles[0]
		elif key==97:
			self.focusTarget = None
		return None
