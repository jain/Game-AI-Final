
import sys, pygame, math, numpy, random, time, copy
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from agents import *
from astarnavigator import *
from clonenav import *

class Castle(Mover):
	def __init__(self, image, position, world, team = None):
		Mover.__init__(self, image, position, 0, 0, world)
		self.team = team
