import sys
import copy
from operator import add
from mapa import *
from consts import Tiles, TILES

class AgentNode:
	def __init__(self, state, parent, key):
		self.state = state
		self.parent = parent
		self.key = key
		self.depth = 0
		self.cost = 0

	def __str__(self):
		return "no(" + str(self.state) + "," + str(self.parent.state) + ")"
	def __repr__(self):
		return str(self)

class SearchAgent:
	def __init__(self, initial_map, destination):
		root = AgentNode(initial_map, None, None)
		self.open_nodes = [root]
		self.destination = destination
		self.solution = None

	def get_path(self, node):
		if node.parent == None:
			return [node.state.__str__()]

		path = self.get_path(node.parent)
		path += [node.state.__str__()]
		return(path)

	def get_keys(self, node):
		if node.parent == None:
			return ""
		keyList = self.get_keys(node.parent)
		keyList += node.key
		return keyList

	def heuristic(self, keeps_pos):
		return pow(keeps_pos[0]-self.destination[0], 2) + pow(keeps_pos[1]-self.destination[1], 2)

	def search(self):
		#count = 0
		while self.open_nodes != []:
			node = self.open_nodes.pop(0)
			keeper_pos = (node.state.keeper[0], node.state.keeper[1])
			#print()
			#print(keeper_pos)
			#print(self.destination)
			#print()
			if (keeper_pos == self.destination):
				#print("We have solved it!")
				#print(self.get_keys(node))
				self.solution = node.state
				return self.get_keys(node)
			
			moves = {"d":[1, 0], "a":[-1, 0], "s":[0, 1], "w":[0, -1]}
			lnewnodes = []

			for key in moves:
				# Se a posição não estiver bloqueada
				new_keeper_pos = [node.state.keeper[0]+moves[key][0], node.state.keeper[1]+moves[key][1]]# ]list(map( add, node.state.keeper, moves[key] ))

				new_tile = node.state.get_tile(new_keeper_pos)
				
				if not node.state.is_blocked(new_keeper_pos) and new_tile != Tiles.BOX and new_tile != Tiles.BOX_ON_GOAL:
					# Criar uma cópia do mapa para ser armazenada no novo node
					new_map = copy.deepcopy(node.state)

					# Alterar a posição do keeper no novo mapa
					#print(node.state.get_tile(new_keeper_pos))
					#####new_map.clear_tile(new_keeper_pos)
					new_map.set_tile(new_keeper_pos, node.state.get_tile(keeper_pos))
					new_map.clear_tile(keeper_pos)

					# Como nunca haverão 2 mapas iguais durante a solução, 
					# caso o novo mapa já tenha aparecido, é ignorado
					
					if not (str(new_map) in self.get_path(node)):#(new_map not in self.get_path(node)):
						#print(new_map)
						newnode = AgentNode(new_map, node, key)
						newnode.depth = node.depth + 1
						newnode.cost = self.heuristic(new_keeper_pos) + newnode.depth
						#print(newnode.cost)
						lnewnodes.append(newnode)
			#print(self.open_nodes)
			# Ao ordenar os nodes, garante que o node com menor custo está à frente na queue
			# e assim será sempre escolhido o node optimal para a solução
			self.open_nodes.extend(lnewnodes)
			self.open_nodes.sort(key = lambda x: x.cost)
			#print(self.open_nodes)
			#count+=1
			#if count == 15:
			#	break
		print("Acabou")

		return None