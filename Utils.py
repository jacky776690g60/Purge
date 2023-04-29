"""Utility Module for the game purge"""
from __future__ import annotations
import os, sys, argparse, timeit, requests, random, copy
from typing import *
from pathlib import Path
from Logger import Logger, DebugLevel
from TermArtist import TermArtist
import heapq


if TYPE_CHECKING:
    from Purge import Cell
    from Characters import Tree

DIRECTIONS_ADJ = [(1,0),(-1,0),(0,1),(0,-1)]
"Directions difference to adjacent cells, [s, w, d, a]"
DIRECTIONS_ALL = DIRECTIONS_ADJ + [(1,1),(-1,1),(1,-1),(-1,-1)]
"Directions difference to adjacent cells (including diaganols)"

def inBounds(i, j, M, N, si=0, sj=0) -> bool:
    """Check if the values are in bounds in terms of a 2D lists
    ## params
        - `i`, `j`: integers to be checked
        - `M`, `N`: upper bounds (exclusive)
        - `si`, `sj`: lower bounds (inclusive, default to 0's)
    """
    if si <= i < M and sj <= j < N: return True
    return False

def isType(elem: object, targetType: Union[type, List[type]]) -> bool:
    """Check if the provided element is of target type"""
    if type(targetType) != list:
        return isinstance(elem, targetType)
    else:
        return type(elem) in targetType


class PathFinder:
    """Class contains functions for finding path between points on the grid"""
    class Node():
        """A node for A star"""
        def __init__(self, position: Tuple[int, int], parent=None):
            self.parent = parent
            self.i, self.j = position[0], position[1]

            self.g = 0
            "distance, cost"
            self.h = 0
            "heuristic, estimated cost"
            self.f = 0
            "score, sum of g(n) + h(n)"
        
        def getPosition(self) -> Tuple[int, int]:
            return (self.i, self.j)

        def __eq__(self, other):
            return self.getPosition() == other.getPosition()

        def __hash__(self) -> int:
            return hash(self.getPosition())

        def __gt__(self, other):
            "Comparing two nodes"
            # return self.getPosition() > other.getPosition() # is after
            # ◼︎ alternative: cannot be directely used as min heap element
            return self.f > other.f


    @staticmethod
    def astar(grid: List[List[Cell]], 
              start: Tuple[int, int], 
              end: Tuple[int, int],
              obstacles: List[Any] = [1]) -> Union[List[Tuple[int,int]], Literal[-1]]:

        def getNeighbors(cur_node: PathFinder.Node) -> List[PathFinder.Node]:
            """ 
            Get a list of neighboring nodes based on current node position
            """
            res: List[PathFinder.Node] = []
            for di, dj in DIRECTIONS_ADJ:
                neiI, neiJ = cur_node.i + di, cur_node.j + dj

                if not inBounds(neiI, neiJ, M, N): continue
                if (grid[neiI][neiJ].peek() in obstacles and (neiI, neiJ) not in [start, end]): continue

                new_node = PathFinder.Node((neiI, neiJ), cur_node)
                res.append(new_node)
            return res

            
        M, N = len(grid), len(grid[0])
        start_node, end_node = PathFinder.Node(start), PathFinder.Node(end)

        minQ: List[PathFinder.Node] = []
        visited: Set[PathFinder.Node] = set()

        # Add the start node
        heapq.heappush(minQ, start_node)

        while minQ:
            cur_node = heapq.heappop(minQ)
            visited.add(cur_node)

            # Found the goal
            if cur_node == end_node:
                path: List[Tuple[int, int]] = []
                ptr = cur_node
                while ptr is not None:
                    path.append(ptr.getPosition())
                    ptr = ptr.parent
                return path[::-1] # Return reversed path

            neighbors = getNeighbors(cur_node)
            for nei in neighbors:
                if nei in visited: continue

                nei.g = cur_node.g + 1
                nei.h = max((nei.i - end_node.i), (nei.j - end_node.j)) + 1
                nei.f = nei.g + nei.h

                for node in minQ:
                    # if the same node but perform worse
                    # if nei == node and nei.g > node.g: continue
                    if nei == node and nei > node: continue

                minQ.append(nei)
        return -1


class DisjointSet():

    class Merger:
        @staticmethod
        def unionFind_merge(grid: List[List[Cell]], targetValue: Any, verbose=False) -> int:
            """Modified version of union find"""
            M, N = len(grid), len(grid[0])
            class UnionFind():
                def __init__(self):
                    self.cnt = 0
                    self.parent = [[(-1,-1)] * N for _ in range(M)]

                    for i in range(M): # set root to itself
                        for j in range(N):
                            if grid[i][j].peek() == targetValue:
                                self.parent[i][j] = (i, j) 
                                self.cnt += 1
                
                def find(self, i, j) -> Tuple[int, int]:
                    if self.parent[i][j] != (i,j):
                        self.parent[i][j] = self.find(*self.parent[i][j])
                    return self.parent[i][j]

                def backprop(self, i, j, val) -> Tuple[int, int]:
                    if (nextPos:= self.parent[i][j]) != (i,j):
                        self.backprop(*nextPos, val)
                    self.parent[i][j] = val
                
                def union(self, pos1: Tuple[int,int], pos2: Tuple[int,int]) -> int:
                    r1, r2 = self.find(*pos1), self.find(*pos2) # two roots
                    if r1 != r2:
                        if r1 <= r2:
                            self.backprop(*r2, r1)
                        else:
                            self.backprop(*r1, r2)
                        self.cnt -= 1 # result of combined two (unfinished) island
            
            uf = UnionFind()
            for i in range(M):
                for j in range(N):
                    if grid[i][j].peek() != targetValue: continue
                    for di, dj in DIRECTIONS_ADJ:
                        if (0<= (newX:=i+di) < M) and (0<= (newY:=j+dj) < N) and grid[newX][newY] == targetValue:
                            uf.union((i,j), (newX, newY))
            
            if verbose: DisjointSet.Merger.printParentMap(uf.parent)
            return uf.cnt

        @staticmethod
        def dfsUnion(grid: List[List[Cell]], targetValue: List[Any], verbose=False):
            M, N = len(grid), len(grid[0])
            roots = set()
            def dfs(x, y):
                nonlocal i, j
                
                if not (0 <= x < M and 0 <= y < N): return
                elif parent[x][y] == (-1,-1): return
                elif parent[x][y] != (x, y): return # already converted

                parent[x][y] = (i, j)
                roots.add((i,j))
                for di, dj in DIRECTIONS_ADJ:
                    dfs(x+di, y+dj)
            
            parent = [[(-1,-1) if not grid[i][j].peek() in targetValue else (i, j) for j in range(N)] for i in range(M)]
            for i in range(M):
                for j in range(N):
                    if len(grid[i][j]) == 0: continue
                    dfs(i, j)

            if verbose: DisjointSet.Merger.printParentMap(parent)
            return roots


        @staticmethod
        def printParentMap(parentList: List[List[Tuple[int,int]]]):
            M, N = len(parentList), len(parentList[0])
            for i in range(M):
                for j in range(N):
                    color = TermArtist.RESET if parentList[i][j] == (-1,-1) else TermArtist.GREEN
                    print(f"{color}{str(parentList[i][j]):<8}", end=" ")
                print()
                    
        
        


if __name__ == '__main__':
    PathFinder.test_astar()

