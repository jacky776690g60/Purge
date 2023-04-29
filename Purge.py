"""
Purge is a terminal-like board game which requires minimum of 2 players. The 
game is inspired by Pendemic and Monopoly. Players will work together to prevent
cities being overrun by the disease. Each player will be given a specific class
which has different ability to cure/block disease accordingly.

The game display requires utf-8. The displayed block may look a bit different on
different OS.
"""
from __future__ import annotations
import os, sys, argparse, timeit, random, warnings
from typing import *
from Logger import Logger, DebugLevel
from TermArtist import TermArtist
from Utils import *

from Characters import *

ALIGN = 3
"Text Alignment"

ecbCh = f"{'□':<{ALIGN}}"
"Empty city block character"
ecbCh_gate = f"{TermArtist.RED}{'□':<{ALIGN}}{TermArtist.RESET}"
"Empty city gate block character"
disCh = f"{TermArtist.GREEN}{'✶':<{ALIGN}}{TermArtist.RESET}"
"Disease block character"
treeCh = f"🌲"
"Tree block character"
knightCh = f"{TermArtist.BLUE}{'🐴':<{ALIGN-1}}{TermArtist.RESET}"
"Knight symbol character"
docCh = f"{'✚':<{ALIGN}}"
"Doctor symbol character"
roadCh = f"{'_':<{ALIGN}}"
"Path symbol character"
nurseCh = f"{TermArtist.BLUE}{'✚':<{ALIGN}}{TermArtist.RESET}"


# =============================
# Fundamental Classes
# =============================
class Cell():
    """A cell is basically a stack, but only store 
        a single instance of the same type of objects
    """
    def __init__(self) -> None:
        self.stk: List[object] = []
        self.LOGGERR = Logger(DebugLevel.INFO)
        self.noUpdateCnt = 0
        """For checking if system can put stuff other than characters in the cell"""

    @property
    def canBeUpdate(self) -> bool:
        return self.noUpdateCnt <= 0

    def __len__(self):
        return len(self.stk)

    def putOnTop(self, val: object):
        "Add to cell"
        if self.getElemFromStack(type(val)):
            self.LOGGERR.warn(f"Cell already contains a: {val.__class__}", )
            return
        self.stk.append(val)

    def pop(self):
        "Pop the top most element unless there is only one left"
        if len(self.stk) == 1: 
            warnings.warn("Cannot pop cell. Reached the base!")
            return None
        return self.stk.pop()
    
    def peek(self):
        "Peek the top most element of the cell"
        if len(self.stk) == 0: return None
        return self.stk[-1]
    
    def peekBase(self):
        "Peek what's the base of this cell (city, tree, or road)"
        if len(self.stk) == 0: return None
        return self.stk[0]

    def getElemFromStack(self, val: type) -> Union[object, None]:
        for el in self.stk:
            if isType(el, val): return el
        return None

    def directRemove(self, k: object) -> None:
        "Directly remove an element from the stack ignoring the order"
        self.stk.remove(k)

    def reset(self):
        "Hard reset stack to empty"
        self.stk: List[str] = []

    def turnEnd(self):
        if self.noUpdateCnt > 0: self.noUpdateCnt -= 1


# =============================
# Main Game Class
# =============================
class Purge():
    """
    Contains core functions of the game Purge.
    """
    def __init__(self, h: int=10, w: int=10, city_count: int=3, city_size: int=5) -> None:
        """ Create a Purge game
            Automatically generate a map and variables for the game
        """
        self.M, self.N = h, w
        "The dimensions of the map, M: height, N: width"
        self.city_count = city_count
        "City count"
        self.city_size = city_size
        "Each city's size"
        self.map = [[Cell() for _ in range(w)] for _ in range(h)]
        "The current map of the Purge game"
        self.doctor: Doctor = None
        "Master character object: doctor"
        self.knight: Knight = None
        "Master character object: knight"
        self.diseaseSeeds: List[Disease] = []
        "All the disease cells in the map"
        self.nurses: List[Nurse] = []
        "A list of all nurses"
        self.trees: List[Tree] = []
        "A list of all trees"
        self.cities = self._generateMap()
        "city objects of the current Purge game"
        

    def _resetToEmptyMap(self):
        "reset back to a completely empty map"
        for i in range(self.M):
            for j in range(self.N):
                self.map[i][j].reset()


    def _generateMap(self) -> List[City]:
        """ Generate a map according to the parameters from constructor """
        LOGGER = Logger(DebugLevel.INFO)
        cls = self.__class__
        map = self.map
        M, N = self.M, self.N

        roots = set() # for validating
        cities: List[City] = []

        while len(roots) != self.city_count:
            LOGGER.debug("Initializing variables for generating new map")
            roots, cities = set(), []
            # CITYNAMES = ["Raccoon City", "Metropolis", "Silent Hill", "San Andreas", "Rhodes", "San Denis", "Chambana"]
            # random.shuffle(CITYNAMES)
            self._resetToEmptyMap()

            LOGGER.debug("Generating new map...")
            for i in range(self.city_count):
                while True:
                    rx, ry = random.randrange(1, M-1), random.randrange(1, N-1) # padding
                    if not self.peekCell(rx,ry): break

                self.putOnMap((rx,ry), (city:= City(self, rx, ry)) )
                cities.append(city)

                LOGGER.debug("Putting in city cells...")
                tryCnt, maxTryCnt = 0, M*N
                while len(city.cells_pos) != self.city_size and tryCnt <= maxTryCnt:
                    i, j = random.choice(list(city.cells_pos))
                    di, dj = random.choice(DIRECTIONS_ADJ)
                    if (inBounds((nI:=i+di), (nJ:=j+dj), M-1, N-1, 1, 1) and
                        not isType(self.peekCell(nI, nJ), City)  
                       ):
                        city.addCellPos((nI, nJ))
                        self.putOnMap((nI,nJ), city)
                    tryCnt += 1
            if tryCnt == maxTryCnt: continue # one of the city failed

            LOGGER.debug("Validating randomly generated cities...")
            roots = DisjointSet.Merger.dfsUnion(map, cities)

        # LOGGER.debug("Finializing cities' initialization")
        # for city in cities: 
        #     city.edgePositions

        LOGGER.debug("Putting stuff in cities")
        roadSet = set()
        for i, city in enumerate(cities):
            LOGGER.debug("Putting master characters and diseases")
            if i == 0:
                pos1, pos2 = list(city.cells_pos)[-2:]
                self.doctor = Doctor(self, pos1)
                self.knight = Knight(self, pos2)
                self.putOnMap(pos1, self.doctor)
                self.putOnMap(pos2, self.knight)
            else:
                pos = list(city.cells_pos)[0]
                diseaseSeed = Disease(self, pos)
                self.diseaseSeeds.append(diseaseSeed)
                map[pos[0]][pos[1]].putOnTop(diseaseSeed)

            LOGGER.debug("Building roads...")
            while True:
                LOGGER.debug("Finding destination...")
                destCity: City = random.choice(cities)
                if city != destCity: break
            
            if not (key:= min((city, destCity), (destCity, city))) in roadSet:
                roadSet.add(key)
            else:
                continue

            foundPath = -1
            while foundPath == -1:  
                LOGGER.debug("Finding path...")
                start = random.choice(city.edgePositions)
                end   = random.choice(destCity.edgePositions)
                foundPath = PathFinder.astar(map, start, end, 
                                                [*cities, self.doctor, self.knight, *self.diseaseSeeds])
                LOGGER.debug((start, end, foundPath))
                
            city.roadsTo[start].append((end, foundPath))
            destCity.roadsTo[end].append((start, foundPath))

            road = Road(self)
            for i, j in foundPath:
                if (i, j) not in [start, end]: map[i][j].putOnTop(road)


        LOGGER.debug("Filling in trees...")
        for i in range(M):
            for j in range(N):
                tree = Tree(self)
                self.trees.append(tree)
                if not map[i][j].peek(): map[i][j].putOnTop(tree)

        return cities

    def peekCell(self, i: int, j: int) -> Union[object, None]:
        "Get the top most elem of the cell on the map at provided position"
        return self.map[i][j].peek()

    def peekCellBase(self, i: int, j: int) -> Union[object, None]:
        "Get the bottom most elem of the cell on the map at provided position"
        return self.map[i][j].peekBase()

    def popFromMap(self, pos: Tuple[int,int]) -> object:
        """pop the most top element at `pos` from the map"""
        return self.map[pos[0]][pos[1]].pop()

    def putOnMap(self, pos: Tuple[int, int], value: Any) -> bool:
        """put an element on the most top at `pos` from the map"""
        self.map[pos[0]][pos[1]].putOnTop(value)

    def moveTopElemOnMapTo(self, original_pos: Tuple[int, int], new_pos: Tuple[int, int]):
        """Pop the top most element at position on the map
            and move that element to the new location
        """
        elem = self.popFromMap(original_pos)
        self.putOnMap(new_pos, elem)

    def searchMapAtPos(self, k: type, i, j) -> Union[object, None]:
        cell = self.map[i][j]
        return cell.getElemFromStack(k)

    def removeElemFromCell(self, k: object, i: int, j: int) -> None:
        "Directly remove an element from cell at provided position on the map"
        if k not in (cell:=self.map[i][j]).stk: raise RuntimeError(f"Cell ({i},{j}) does not have element: {k.__class__}")
        cell.directRemove(k)

    def removeTypeFromCell(self, k: type, i: int, j: int) -> None:
        "Directly remove a type from cell at provided position on the map"
        for elem in (cell:=self.map[i][j]).stk:
            if type(elem) == k:
                cell.directRemove(elem)
    
    def roundEnd(self, actualEnd=True) -> int:
        """Mark the end of a full turn end for the current purge game
            Should be called after each player finish their turn
        ### return
            - bool: win=1, lose=-1, still_playing=0
        """
        overRunCities = set()
        if actualEnd:
            # ◼︎ processing diseases
            for city in self.cities:
                if (seeds:=city.edgeDiseases):
                    pickedDisease_seed = random.choice(seeds)
                    pickedDisease_seed.growToAdjacent()
                if city.getInfectPercentage() > 0.6:
                    overRunCities.add(city)
                elif city in overRunCities:
                    overRunCities.remove(city)

            for row in self.map:
                for cell in row:
                    cell.turnEnd()

            for nurse in self.nurses:
                if isType(nurse, Nurse): nurse.turnEnd()

        
        
        # ◼︎ checking win/lose condition
        if len(overRunCities) == self.city_count:
            return -1
        elif len(self.diseaseSeeds) == 0:
            return 1
        return 0


    def showMap(self):
        """Display the current map and the status of the game so far"""
        cls = self.__class__
        map = self.map
        M, N = self.M, self.N

        print(" " * ALIGN, end="")
        for cIdx in range(N):
            print(f"{cIdx:<{ALIGN}}", end="")
        print()

        for i in range(M):
            print(f"{i:<{ALIGN}}", end="")
            for j in range(N):
                mostTopObj = map[i][j].peek()
                ch = " "
                if isType(mostTopObj, City):
                    ch = ecbCh_gate if mostTopObj.isGate(i, j) else ecbCh
                    if not map[i][j].canBeUpdate:
                        ch = f"{TermArtist.MEGANTA}{ch}{TermArtist.RESET}"
                    else:
                        ch = f"{TermArtist.YELLOW}{ch}{TermArtist.RESET}"
                elif isType(mostTopObj, Doctor):
                    ch = docCh
                elif isType(mostTopObj, Nurse):
                    ch = nurseCh
                elif isType(mostTopObj, Knight):
                    ch = knightCh
                elif isType(mostTopObj, Disease):
                    ch = disCh
                elif isType(mostTopObj, Tree):
                    ch = treeCh
                elif isType(mostTopObj, Road):
                    ch = roadCh

                print(f"{ch:<{ALIGN-1}}", end="")
            print()


# =============================
# Starting a game
# =============================






if __name__ == "__main__":
    purge = Purge(12, 12, 3, 15)
    purge.showMap()