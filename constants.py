'''
 * Copyright (c) 2014, 2015 Entertainment Intelligence Lab, Georgia Institute of Technology.
 * Originally developed by Mark Riedl.
 * Last edited by Matthew Guzdial 01/2016
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

SCREEN = [1024, 768]
WORLD = [1024, 768]
TICK = 60

SPEED = (5, 5)
NUMOBSTACLES = 3
OBSTACLERADIUS = 200
OBSTACLESIGMA = 50
OBSTACLEMIN = 25
OBSTACLEPOINTS = 7
OBSTACLEGRIDSIZE = 50
NUMRESOURCES = 20
SEED = 2
HITPOINTS = 25
BASEHITPOINTS = 750
TOWERHITPOINTS = 50

SPAWNERHITPOINTS = 75
DEFENSEHITPOINTS = 150
SUPPORTHITPOINTS = 50
OFFSET = 20
PERCENTFIELD = 0.45

AGENT = "sprites/spartan2.gif"
SMALLBULLET = "sprites/bullet.gif"
BIGBULLET = "sprites/bullet2.gif"
RESOURCE = "sprites/crystal.gif"
GATE = "sprites/mine.gif"
NPC = "sprites/spartan.gif"
JACKAL = "sprites/jackal.gif"
ELITE = "sprites/elite.gif"
CRATE = "sprites/crate.gif"
BASE = "sprites/base.gif"
CRYSTAL = "sprites/crystal.gif"
TREE = "sprites/tree.gif"
MINE = "sprites/mine.gif"
TOWER = "sprites/tower.gif"
FACTORY1 = "sprites/factory.gif"
FACTORY2 = "sprites/factory2.png"
FACTORY3 = "sprites/factory3.png"

SMALLBULLETSPEED = (20, 20)
SMALLBULLETDAMAGE = 1
BIGBULLETSPEED = (20, 20)
BIGBULLETDAMAGE = 5
FIRERATE = 10
DODGERATE = 10
BUILDRADIUS = 120

INFINITY = float("inf")
EPSILON = 0.000001

ADCMINION_KILL = 50
TANKMINION_KILL = 100
AOEMINION_KILL = 200
AOEWARRIOR_KILL = 200