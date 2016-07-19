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
from moba2 import *
from btnode import *

###########################
### SET UP BEHAVIOR TREE


def treeSpec(agent):
	myid = str(agent.getTeam())
	spec = None
	### YOUR CODE GOES BELOW HERE ###
		
	spec = \
	[(Selector, 'root'),\
		# If at or below 50% health, retreat (somewhat conservative on health after enemy kill, if needed)
		(Retreat, 0.5, 'retreat'),\
		# Once in this branch, do not abort unless health is below 25%
		[(HitpointDaemon, 0.25, 'healthy enough'),\
			# Find an enemy or, if one is close enough, kill an enemy
			[(Selector, 'chase or kill'),\
				# So long as no enemy is nearby, seek an enemy
				[(NoEnemyNearby, 'no enemy nearby'),\
					[(Selector, 'chase a target'),\
						# If not as strong as the enemy hero, avoid seeking a fight you can't win
						[(BuffDaemon, -1, 'buff enough'),
							(ChaseHero, 'chase hero')\
						],\
						(ChaseMinion, 'chase minion')\
					]
				],
				# If an enemy is nearby, kill them (ignores disadvantage against heroes to keep pressure up)
				[(Selector, 'kill a target'),\
					(EvadeAndKillHero, 'kill hero'),\
					(EvadeAndKillMinion, 'kill minion')\
				]
			]\
		]
	]
	
	### YOUR CODE GOES ABOVE HERE ###
	return spec

def myBuildTree(agent):
	myid = str(agent.getTeam())
	root = None
	### YOUR CODE GOES BELOW HERE ###
	
	### YOUR CODE GOES ABOVE HERE ###
	return root

### Helper function for making BTNodes (and sub-classes of BTNodes).
### type: class type (BTNode or a sub-class)
### agent: reference to the agent to be controlled
### This function takes any number of additional arguments that will be passed to the BTNode and parsed using BTNode.parseArgs()
def makeNode(type, agent, *args):
	node = type(agent, args)
	return node

###############################
### BEHAVIOR CLASSES:


##################
### Taunt
###
### Print disparaging comment, addressed to a given NPC
### Parameters:
###   0: reference to an NPC
###   1: node ID string (optional)

class Taunt(BTNode):

	### target: the enemy agent to taunt

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the target
		if len(args) > 0:
			self.target = args[0]
		# Second argument is the node ID
		if len(args) > 1:
			self.id = args[1]

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target is not None:
			print "Hey", self.target, "I don't like you!"
		return ret

##################
### MoveToTarget
###
### Move the agent to a given (x, y)
### Parameters:
###   0: a point (x, y)
###   1: node ID string (optional)

class MoveToTarget(BTNode):
	
	### target: a point (x, y)
	
	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the target
		if len(args) > 0:
			self.target = args[0]
		# Second argument is the node ID
		if len(args) > 1:
			self.id = args[1]

	def enter(self):
		BTNode.enter(self)
		self.agent.navigateTo(self.target)

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None:
			# failed executability conditions
			print "exec", self.id, "false"
			return False
		elif distance(self.agent.getLocation(), self.target) < self.agent.getRadius():
			# Execution succeeds
			print "exec", self.id, "true"
			return True
		else:
			# executing
			return None
		return ret

##################
### Retreat
###
### Move the agent back to the base to be healed
### Parameters:
###   0: percentage of hitpoints that must have been lost to retreat
###   1: node ID string (optional)


class Retreat(BTNode):
	
	### percentage: Percentage of hitpoints that must have been lost
	
	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.percentage = 0.5
		# First argument is the factor
		if len(args) > 0:
			self.percentage = args[0]
		# Second argument is the node ID
		if len(args) > 1:
			self.id = args[1]

	def enter(self):
		BTNode.enter(self)
		self.agent.navigateTo(self.agent.world.getBaseForTeam(self.agent.getTeam()).getLocation())
	
	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.agent.getHitpoints() > self.agent.getMaxHitpoints() * self.percentage:
			# fail executability conditions
			print "exec", self.id, "false"
			return False
		elif self.agent.getHitpoints() == self.agent.getMaxHitpoints():
			# Exection succeeds
			print "exec", self.id, "true"
			return True
		else:
			# executing
			return None
		return ret

##################
### ChaseMinion
###
### Find the closest minion and move to intercept it.
### Parameters:
###   0: node ID string (optional)


class ChaseMinion(BTNode):

	### target: the minion to chase
	### timer: how often to replan

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		self.timer = 50
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.timer = 50
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		if len(enemies) > 0:
			best = None
			dist = 0
			for e in enemies:
				if isinstance(e, Minion):
					d = distance(self.agent.getLocation(), e.getLocation())
					if best == None or d < dist:
						best = e
						dist = d
			self.target = best
		if self.target is not None:
			navTarget = self.chooseNavigationTarget()
			if navTarget is not None:
				self.agent.navigateTo(navTarget)


	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or self.target.isAlive() == False:
			# failed execution conditions
			print "exec", self.id, "false"
			return False
		elif distance(self.agent.getLocation(), self.target.getLocation()) < BIGBULLETRANGE:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			# executing
			self.timer = self.timer - 1
			if self.timer <= 0:
				self.timer = 50
				navTarget = self.chooseNavigationTarget()
				if navTarget is not None:
					self.agent.navigateTo(navTarget)
			return None
		return ret

	def chooseNavigationTarget(self):
		if self.target is not None:
			return self.target.getLocation()
		else:
			return None

##################
### KillMinion
###
### Kill the closest minion. Assumes it is already in range.
### Parameters:
###   0: node ID string (optional)


class KillMinion(BTNode):

	### target: the minion to shoot

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.agent.stopMoving()
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		if len(enemies) > 0:
			best = None
			dist = 0
			for e in enemies:
				if isinstance(e, Minion):
					d = distance(self.agent.getLocation(), e.getLocation())
					if best == None or d < dist:
						best = e
						dist = d
			self.target = best


	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or distance(self.agent.getLocation(), self.target.getLocation()) > BIGBULLETRANGE:
			# failed executability conditions
			print "exec", self.id, "false"
			return False
		elif self.target.isAlive() == False:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			# executing
			self.shootAtTarget()
			return None
		return ret

	def shootAtTarget(self):
		if self.agent is not None and self.target is not None:
			self.agent.turnToFace(self.target.getLocation())
			self.agent.shoot()


##################
### ChaseHero
###
### Move to intercept the enemy Hero.
### Parameters:
###   0: node ID string (optional)

class ChaseHero(BTNode):

	### target: the hero to chase
	### timer: how often to replan

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		self.timer = 50
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.timer = 50
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		for e in enemies:
			if isinstance(e, Hero):
				self.target = e
				navTarget = self.chooseNavigationTarget()
				if navTarget is not None:
					self.agent.navigateTo(navTarget)
				return None


	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or self.target.isAlive() == False:
			# fails executability conditions
			print "exec", self.id, "false"
			return False
		elif distance(self.agent.getLocation(), self.target.getLocation()) < BIGBULLETRANGE:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			# executing
			self.timer = self.timer - 1
			if self.timer <= 0:
				self.timer = 50
				navTarget = self.chooseNavigationTarget()
				if navTarget is not None:
					self.agent.navigateTo(navTarget)
			return None
		return ret

	def chooseNavigationTarget(self):
		if self.target is not None:
			return self.target.getLocation()
		else:
			return None

##################
### KillHero
###
### Kill the enemy hero. Assumes it is already in range.
### Parameters:
###   0: node ID string (optional)


class KillHero(BTNode):

	### target: the minion to shoot

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.agent.stopMoving()
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		for e in enemies:
			if isinstance(e, Hero):
				self.target = e
				return None

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or distance(self.agent.getLocation(), self.target.getLocation()) > BIGBULLETRANGE:
			# failed executability conditions
			if self.target == None:
				print "foo none"
			else:
				print "foo dist", distance(self.agent.getLocation(), self.target.getLocation())
			print "exec", self.id, "false"
			return False
		elif self.target.isAlive() == False:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			#executing
			self.shootAtTarget()
			return None
		return ret

	def shootAtTarget(self):
		if self.agent is not None and self.target is not None:
			self.agent.turnToFace(self.target.getLocation())
			self.agent.shoot()


##################
### HitpointDaemon
###
### Only execute children if hitpoints are above a certain threshold.
### Parameters:
###   0: percentage of hitpoints that must have been lost to fail the daemon check
###   1: node ID string (optional)


class HitpointDaemon(BTNode):
	
	### percentage: percentage of hitpoints that must have been lost to fail the daemon check
	
	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.percentage = 0.5
		# First argument is the factor
		if len(args) > 0:
			self.percentage = args[0]
		# Second argument is the node ID
		if len(args) > 1:
			self.id = args[1]

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.agent.getHitpoints() < self.agent.getMaxHitpoints() * self.percentage:
			# Check failed
			print "exec", self.id, "fail"
			return False
		else:
			# Check didn't fail, return child's status
			return self.getChild(0).execute(delta)
		return ret

##################
### BuffDaemon
###
### Only execute children if agent's level is significantly above enemy hero's level.
### Parameters:
###   0: Number of levels above enemy level necessary to not fail the check
###   1: node ID string (optional)

class BuffDaemon(BTNode):

	### advantage: Number of levels above enemy level necessary to not fail the check

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.advantage = 0
		# First argument is the advantage
		if len(args) > 0:
			self.advantage = args[0]
		# Second argument is the node ID
		if len(args) > 1:
			self.id = args[1]

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		hero = None
		# Get a reference to the enemy hero
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		for e in enemies:
			if isinstance(e, Hero):
				hero = e
				break
		if hero == None or self.agent.level <= hero.level + self.advantage:
			# fail check
			print "exec", self.id, "fail"
			return False
		else:
			# Check didn't fail, return child's status
			return self.getChild(0).execute(delta)
		return ret





#################################
### MY CUSTOM BEHAVIOR CLASSES

##################
### NoEnemyNearby
###
### Returns True if not within range of an enemy. Returns False if we are.
### Parameters:
###   0: node ID string (optional)

class NoEnemyNearby(BTNode):

	### advantage: Number of levels above enemy level necessary to not fail the check

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		enemyNearby = False
		# Check all enemies to assess if any are nearby
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		for e in enemies:
			if e in self.agent.getVisible() and distance(self.agent.getLocation(), e.getLocation()) < BIGBULLETRANGE:
				return False
				break
		
		# Check didn't fail, return child's status
		return self.getChild(0).execute(delta)
		
		return ret



##################
### EvadeAndKillHero
###
### Kill the enemy hero while moving around semi-randomly to avoid most shots. Assumes it is already in range.
### Parameters:
###   0: node ID string (optional)


class EvadeAndKillHero(BTNode):

	### target: the minion to shoot

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.agent.stopMoving()
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		for e in enemies:
			if isinstance(e, Hero) and e in self.agent.getVisible():
				self.target = e
				return None

	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or self.target not in self.agent.getVisible() or distance(self.agent.getLocation(), self.target.getLocation()) > BIGBULLETRANGE:
			# failed executability conditions
			if self.target == None:
				print "foo none"
			else:
				print "foo dist", distance(self.agent.getLocation(), self.target.getLocation())
			print "exec", self.id, "false"
			return False
		elif self.target.isAlive() == False:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			#executing
			if self.agent.getMoveTarget() == None:
				self.setDestination()
			self.shootAtTarget()
			return None
		return ret
	
	def setDestination(self):
		#if not moving, find place to move to
		enemy = self.target.getLocation()
		agent = self.agent
		pos = agent.getLocation()
		# find location within shooting distance of target and move toward it
		x = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
		y = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
		goal = (enemy[0] + x, enemy[1] + y)
		ang = math.degrees(angle((enemy[0] - pos[0], enemy[1] - pos[1]), (goal[0] - pos[0], goal[1] - pos[1])))
		# Check that we are not moving out of shooting range, too close to the target, our destination won't be too
		#   close to a wall, or that our route won't cross right through our foe
		while x*x + y*y >= BIGBULLETRANGE*BIGBULLETRANGE or x*x + y*y <= BIGBULLETRANGE*BIGBULLETRANGE/4\
			or self.isInvalidLocation(goal) or not clearShot(pos, goal, agent.world.getLinesWithoutBorders(), None, agent)\
			or ang < 45 or ang > 135:
				x = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
				y = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
				goal = (enemy[0] + x, enemy[1] + y)
				ang = math.degrees(angle((enemy[0] - pos[0], enemy[1] - pos[1]), (goal[0] - pos[0], goal[1] - pos[1])))
		agent.navigateTo(goal)
	
	def shootAtTarget(self):
		if self.agent is not None and self.target is not None:
			aim = self.target.getLocation()
			if self.target.isMoving():
				unwound = self.target.orientation
				if unwound < 0:
					unwound = unwound + 360.0
				rad = math.radians(unwound)
				normalizedDirection = (math.cos(rad), -math.sin(rad))
				next = [m*n for m,n in zip(normalizedDirection, self.target.speed)]
				aim = (aim[0] + next[0]*10, aim[1] + next[1]*10)
			self.agent.turnToFace(aim)
			self.agent.shoot()
	
	def isInvalidLocation(self, position):
		for l in self.agent.world.getLinesWithoutBorders():
			if minimumDistance(l, position) < self.agent.getMaxRadius():
				return True
		return False


##################
### EvadeAndKillMinion
###
### Kill the closest minion while moving around semi-randomly to avoid most shots. Assumes it is already in range.
### Parameters:
###   0: node ID string (optional)


class EvadeAndKillMinion(BTNode):

	### target: the minion to shoot

	def parseArgs(self, args):
		BTNode.parseArgs(self, args)
		self.target = None
		# First argument is the node ID
		if len(args) > 0:
			self.id = args[0]

	def enter(self):
		BTNode.enter(self)
		self.agent.stopMoving()
		enemies = self.agent.world.getEnemyNPCs(self.agent.getTeam())
		if len(enemies) > 0:
			best = None
			dist = 0
			for e in enemies:
				if isinstance(e, Minion) and e in self.agent.getVisible():
					d = distance(self.agent.getLocation(), e.getLocation())
					if best == None or d < dist:
						best = e
						dist = d
			self.target = best


	def execute(self, delta = 0):
		ret = BTNode.execute(self, delta)
		if self.target == None or self.target not in self.agent.getVisible() or distance(self.agent.getLocation(), self.target.getLocation()) > BIGBULLETRANGE:
			# failed executability conditions
			print "exec", self.id, "false"
			return False
		elif self.target.isAlive() == False:
			# succeeded
			print "exec", self.id, "true"
			return True
		else:
			#executing
			if self.agent.getMoveTarget() == None:
				self.setDestination()
			self.shootAtTarget()
			return None
		return ret
	
	def setDestination(self):
		#if not moving, find place to move to
		enemy = self.target.getLocation()
		agent = self.agent
		pos = agent.getLocation()
		# find location within shooting distance of target and move toward it
		x = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
		y = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
		goal = (enemy[0] + x, enemy[1] + y)
		ang = math.degrees(angle((enemy[0] - pos[0], enemy[1] - pos[1]), (goal[0] - pos[0], goal[1] - pos[1])))
		# Check that we are not moving out of shooting range, too close to the target, our destination won't be too
		#   close to a wall, or that our route won't cross right through our foe
		while x*x + y*y >= BIGBULLETRANGE*BIGBULLETRANGE or x*x + y*y <= BIGBULLETRANGE*BIGBULLETRANGE/4\
			or self.isInvalidLocation(goal) or not clearShot(pos, goal, agent.world.getLinesWithoutBorders(), None, agent)\
			or ang < 45 or ang > 135:
				x = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
				y = random.randrange(-BIGBULLETRANGE, BIGBULLETRANGE)
				goal = (enemy[0] + x, enemy[1] + y)
				ang = math.degrees(angle((enemy[0] - pos[0], enemy[1] - pos[1]), (goal[0] - pos[0], goal[1] - pos[1])))
		agent.navigateTo(goal)

	def shootAtTarget(self):
		if self.agent is not None and self.target is not None:
			aim = self.target.getLocation()
			if self.target.isMoving():
				unwound = self.target.orientation
				if unwound < 0:
					unwound = unwound + 360.0
				rad = math.radians(unwound)
				normalizedDirection = (math.cos(rad), -math.sin(rad))
				next = [m*n for m,n in zip(normalizedDirection, self.target.speed)]
				aim = (aim[0] + next[0]*10, aim[1] + next[1]*10)
			self.agent.turnToFace(aim)
			self.agent.shoot()
	
	def isInvalidLocation(self, position):
		for l in self.agent.world.getLinesWithoutBorders():
			if minimumDistance(l, position) < self.agent.getMaxRadius():
				return True
		return False
