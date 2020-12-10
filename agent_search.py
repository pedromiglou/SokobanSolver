from operator import add
from consts import Tiles
import asyncio
from bisect import insort_left

class AgentNode:
	def __init__(self, state, parent, key, heuristic):
		self.state = state
		self.parent = parent
		self.key = key
		#self.depth = depth
		#self.cost = cost
		self.heuristic = heuristic

	def __str__(self):
		return "no(" + str(self.state) + "," + str(self.parent.state) + ")"

	#funcao para fazer sort sem usar sempre key
	def __lt__(self, other):
		return self.heuristic < other.heuristic


class SearchAgent:
	def __init__(self, isWall):
		self.isWall = isWall

	def get_keys(self, node):
		if node.parent == None:
			return ""
		return self.get_keys(node.parent) + node.key

	async def search(self, boxes, initial_pos, destination):
		root = AgentNode(initial_pos, None, None, None)
		open_nodes = [root]
		self.visitedNodes = set()
		self.visitedNodes.add(initial_pos)
		await asyncio.sleep(0) # this should be 0 in your code and this is REQUIRED

		while open_nodes != []:
			node = open_nodes.pop(0)

			if node.state == destination:
				return self.get_keys(node)
			
			moves = [("d", 1, 0), ("a", -1, 0), ("s", 0, 1), ("w", 0, -1)]

			for key, movX, movY in moves:
				new_keeper_pos = (node.state[0]+movX, node.state[1]+movY)
				
				# Se a posição não estiver bloqueada
				if not self.isWall[new_keeper_pos[0]][new_keeper_pos[1]] and new_keeper_pos not in boxes:

					# não podem haver dois conjuntos de coordenadas iguais na solução
					#if not self.state_in_path(node, new_keeper_pos):
					if new_keeper_pos not in self.visitedNodes:
						self.visitedNodes.add(new_keeper_pos)
						newnode = AgentNode(new_keeper_pos, node, key, abs(new_keeper_pos[0]-destination[0]) + abs(new_keeper_pos[1]-destination[1]))

						# Ao ordenar os nodes, garante que o node com menor custo está à frente na queue
						# e assim será sempre escolhido o node optimal para a solução
						insort_left(open_nodes, newnode)

		return None