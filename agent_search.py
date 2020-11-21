from operator import add
from consts import Tiles
import asyncio
from bisect import insort_left

class AgentNode:
	def __init__(self, state, parent, key, depth, cost, heuristic):
		self.state = state
		self.parent = parent
		self.key = key
		self.depth = depth
		self.cost = cost
		self.heuristic = heuristic

	def __str__(self):
		return "no(" + str(self.state) + "," + str(self.parent.state) + ")"

	#funcao para fazer sort sem usar sempre key
	def __lt__(self, other):
		return self.cost + 2*self.heuristic < other.cost + 2*other.heuristic


class SearchAgent:
	def __init__(self, initial_map, destination):
		self.map = initial_map
		self.destination = destination
		root = AgentNode(initial_map.keeper, None, None, 0, 0, self.heuristic(initial_map.keeper))
		self.open_nodes = [root]

	def state_in_path(self, node, newstate):
		if node.state == newstate:
			return True
		else:
			if node.parent != None:
				return self.state_in_path(node.parent, newstate)
			else:
				return False

	def get_keys(self, node):
		if node.parent == None:
			return ""
		keyList = self.get_keys(node.parent)
		keyList += node.key
		return keyList

	def heuristic(self, keeps_pos):
		return abs(keeps_pos[0]-self.destination[0]) + abs(keeps_pos[1]-self.destination[1])

	async def search(self):
		while self.open_nodes != []:
			node = self.open_nodes.pop(0)

			if node.state == self.destination:
				if self.map.keeper != node.state:
					self.map.clear_tile(self.map.keeper)
					self.map.set_tile(node.state, Tiles.MAN)

				return self.get_keys(node)
			
			moves = {"d":[1, 0], "a":[-1, 0], "s":[0, 1], "w":[0, -1]}

			await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

			for key in moves:
				new_keeper_pos = (node.state[0]+moves[key][0], node.state[1]+moves[key][1])

				new_tile = self.map.get_tile(new_keeper_pos)
				
				# Se a posição não estiver bloqueada
				if not self.map.is_blocked(new_keeper_pos) and new_tile != Tiles.BOX and new_tile != Tiles.BOX_ON_GOAL:

					# não podem haver dois conjuntos de coordenadas iguais na solução
					if not self.state_in_path(node, new_keeper_pos):
						newnode = AgentNode(new_keeper_pos, node, key, node.depth+1, node.cost+1, self.heuristic(new_keeper_pos))

						# Ao ordenar os nodes, garante que o node com menor custo está à frente na queue
						# e assim será sempre escolhido o node optimal para a solução
						insort_left(self.open_nodes, newnode)

		return None