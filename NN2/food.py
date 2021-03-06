import random
from constants import *
from abstract import ParentSprite
import pygame


class Food(ParentSprite):
	""" 
	Represents a piece of food in our game. Inherits from ParentSprite
	"""


	def __init__(self, model, dna=None):
		""" 
		Initializes a food object to a specified center and radius. 
		"""
		self.radius = FOOD_MAX_RADIUS
		super(Food, self).__init__(model, dna)
		self.radius = FOOD_START_RADIUS

		self.color = FOOD_COLOR
		self.eaten = False


	def update(self, model):

		if self.radius < FOOD_MAX_RADIUS:
			self.radius += FOOD_GROWTH_RATE

		else:
			self.reproduce_asexually(model)
			self.radius = FOOD_START_RADIUS


	def reproduce_asexually(self, model):

		number_of_children = np.random.randint(1,4)
		children = []
		for c in range(number_of_children):
			child = self.reproduce(model)
			if child['found_spot']:
				children.append(child)

		for child in children:
			model.foods.append(Food(model, child))



