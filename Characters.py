from __future__ import annotations
import os, sys, argparse, timeit, random, warnings
from typing import *
from Logger import Logger, DebugLevel
from TermArtist import TermArtist
from Utils import *

if TYPE_CHECKING:
    from Purge import Purge, Cell

class PawnBase():
    def __init__(self, purge: Purge, pos: Tuple[int, int]) -> None:
        self.root = pos
        "The current (center) position of this pawn"
        self.purgeRef = purge
        "A reference to a Purge game"

    def turnEnd(self):
        raise NotImplementedError


class City(PawnBase):
    """
    This class represents a single city and contains functions related to 
    modifying or getting the info of that city.
    """
    def __init__(self, purge: Purge, rx: int, ry: int, cityName="Default CityName") -> None:
        super().__init__(purge, (rx, ry))
        self.cityName = cityName
        "name of the city"
        self.cells_pos: Set[Tuple[int, int]] = set()
        "A set of positions that belongs to the city and correspond to the map"
        self.roadsTo: Dict[Tuple[int,int], List[Tuple[Tuple, List[Tuple]]]] = DefaultDict(list)
        """A dict of roads that connect to other cities
        - Key = start_pos, Value = [(end_position, path)]
        """

        self.addCellPos(self.root)

    def __hash__(self) -> int:
        return hash((*self.root, self.cityName))

    def __gt__(self, other: City) -> bool:
        return (*self.root, self.cityName) > (*other.root, other.cityName)


    @property
    def edgePositions(self) -> List[Cell]:
        """get the positions of the edges of this city"""
        M, N = self.purgeRef.M, self.purgeRef.N
        candidates = DefaultDict(list)

        for i, j in self.cells_pos:
            for di, dj in DIRECTIONS_ADJ:
                if not inBounds((ni:=i+di), (nj:=j+dj), M, N) or\
                   isType(self.purgeRef.peekCell(ni, nj), City): continue
                candidates[(ni,nj)].append((i,j))
        
        res = []
        for ls in candidates.values():
            if len(ls) > 3: continue
            for v in ls:
                res.append(v)
        return res

    @property
    def gatePositions(self) -> List[Tuple[int, int]]:
        """Return the positions of all the gates in this city"""
        return self.roadsTo.keys()

    @property
    def edgeDiseases(self) -> List[Disease]:
        """Get all the diseases that are at the edge of each disease blob"""
        purge, M, N, res = self.purgeRef, self.purgeRef.M, self.purgeRef.N, []
        for pos in self.cells_pos:
            topMostObj = purge.peekCell(*pos)
            botMostObj = purge.peekCellBase(*pos)
            if isType(topMostObj, Disease):
                for di, dj in DIRECTIONS_ADJ:
                    if inBounds((ni:=pos[0]+di), (nj:=pos[1]+dj), M, N) and\
                        (isType(purge.peekCell(ni, nj), City) or 
                         (isType(purge.peekCell(ni, nj), Road) and botMostObj.isGate(*pos) )
                        ):
                        res.append(topMostObj)
                        break
        return res

    def addCellPos(self, pos: Tuple[int, int]) -> None:
        """ Add a coordinate to the cell position set """
        self.cells_pos.add(pos)

    def isGate(self, i: int, j: int) -> bool:
        """Check if the position is a gate of this city"""
        return (i,j) in self.roadsTo.keys()

    def getInfectPercentage(self) -> float:
        diseaseCnt = 0
        for pos in self.cells_pos:
            topMostObj = self.purgeRef.peekCell(*pos)
            if isType(topMostObj, Disease):
                diseaseCnt += 1
        return round(diseaseCnt / len(self.cells_pos), 2)

# =============================
# User Character Classes
# =============================
class Tree(PawnBase):
    def __init__(self, purge: Purge) -> None:
        super().__init__(purge, (-1, -1))


class Road(PawnBase):
    def __init__(self, purge: Purge) -> None:
        super().__init__(purge, (-1, -1))


class MasterPawn(PawnBase):
    def __init__(self, purge: Purge, pos: Tuple[int, int]) -> None:
        super().__init__(purge, pos)

    def moveTo(self, pos: Tuple[int, int]) -> bool:
        """Move master character to the specified position
        ### return
            - `bool`: `True` if moving was successfuly, `False` if not
        """
        purge, map = self.purgeRef, self.purgeRef.map
        if not inBounds(*pos, self.purgeRef.M, self.purgeRef.N): return False
        if not type(map[pos[0]][pos[1]].peek()) in [City, Road]: return False

        if purge.peekCellBase(*self.root).isGate(*self.root) and\
            isType(purge.peekCell(*pos), Road):
            gate: City = purge.peekCellBase(*self.root)
            if len(gate.roadsTo[self.root]) == 1:
                nextPos = gate.roadsTo[self.root][0][0]
                purge.moveTopElemOnMapTo(self.root, nextPos)
                self.root = nextPos
            else:
                print("Pick a destination:")
                for i, endSeq in enumerate(gate.roadsTo[self.root]):
                    print(i, endSeq[0])
                while not 0 <= (val:= int(input())) < len(gate.roadsTo[self.root]):
                    continue
                nextPos = gate.roadsTo[self.root][val][0]
                print(nextPos)
                purge.moveTopElemOnMapTo(self.root, nextPos)
                self.root = nextPos
            return True
        else:
            if type(map[pos[0]][pos[1]].peek()) == City:
                purge.moveTopElemOnMapTo(self.root, pos)
                self.root = pos
                return True
            else: return False

    def moveDirectionalByOne(self, val: Literal["w","s","a","d"]) -> bool:
        """Move directionally by one cell
        ## param
            - `dir`: 1: left, 2: up, 3 : right, 4: down
        """
        val = val.lower()
        diff = None
        for ch, dv in zip(["s","w","d","a"], DIRECTIONS_ADJ):
            if val == ch: diff = dv
        if diff == None: raise RuntimeError("Incorrect val for directional movement")
        newPos = tuple(map(sum, zip(self.root, diff)) )
        self.moveTo(newPos)

class MasterPawnSecondary(PawnBase):
    def __init__(self, purge: Purge, master_pos: Tuple[int, int], pos: Tuple[int, int]) -> None:
        super().__init__(purge, pos)
        self.delta = tuple(map(lambda i, j: i - j, master_pos, pos))


class Doctor(MasterPawn):
    def __init__(self, purge: Purge, pos: Tuple[int, int]) -> None:
        super().__init__(purge, pos)

    def cureCross(self):
        purge, M, N = self.purgeRef, self.purgeRef.M, self.purgeRef.N
        
        def checkAndRemove(k, isVertical):
            for v in range(k):
                checkPos = (v, self.root[1]) if isVertical else (self.root[0], v)
                if not purge.peekCellBase(*checkPos) is purge.peekCellBase(*self.root): continue
                   
                diseaseSeed: Disease = purge.searchMapAtPos(Disease, *checkPos)
                if diseaseSeed == None: continue

                purge.diseaseSeeds.remove(diseaseSeed)
                purge.removeElemFromCell(diseaseSeed, *checkPos)
                purge.map[checkPos[0]][checkPos[1]].noUpdateCnt += 2
        checkAndRemove(M, isVertical=True)
        checkAndRemove(N, isVertical=False)
            
    def placeNurse(self):
        print("pick a direction to place nurse:")
        selectionDict = {}
        i = 0
        for dir in DIRECTIONS_ADJ:
            newPos = tuple(map(sum, zip(self.root, dir)))
            if isType(self.purgeRef.peekCell(*newPos), City):
                print(f"{i}.", newPos)
                selectionDict[str(i)] = newPos
                i += 1
        
        selection = input("Number: ")
        if selection in selectionDict:
            nursePos = selectionDict[selection]
            if (self.purgeRef.peekCellBase(*nursePos), City):
                nurse = Nurse(self.purgeRef, self.root, nursePos)
                self.purgeRef.putOnMap(nursePos, nurse)
                self.purgeRef.nurses.append(nurse)

class Nurse(MasterPawnSecondary):
    def __init__(self, purge: Purge, master_pos: Tuple[int, int], pos: Tuple[int, int]) -> None:
        super().__init__(purge, master_pos, pos)
        self.counter = 2

    def turnEnd(self):
        purge = self.purgeRef
        for dir in DIRECTIONS_ALL:
            curePos = tuple(map(sum, zip(self.root, dir)))
            if inBounds(*curePos, self.purgeRef.M, self.purgeRef.N) and\
                isType(self.purgeRef.peekCellBase(*curePos), City):
                diseaseSeed: Disease = purge.searchMapAtPos(Disease, *curePos)
                if diseaseSeed == None: continue
                purge.diseaseSeeds.remove(diseaseSeed)
                purge.removeElemFromCell(diseaseSeed, *curePos)
                purge.map[curePos[0]][curePos[1]].noUpdateCnt += 2
        self.counter -= 1
        if self.counter <= 0:
            self.purgeRef.removeElemFromCell(self, *self.root)
            idx = self.purgeRef.nurses.index(self)
            self.purgeRef.nurses[idx] = None


class Knight(MasterPawn):
    def __init__(self, purge: Purge, pos: Tuple[int, int]) -> None:
        super().__init__(purge, pos)

    def throwDisinfectant(self):
        purge, M, N = self.purgeRef, self.purgeRef.M, self.purgeRef.N
        selectionDict = {}
        i = 0
        try:
            print("Pick a position to throw the disinfectant, it will effect the adjacent 9 cells.")
            for di, dj in DIRECTIONS_ALL:
                centPos = tuple(map(sum, zip(self.root, (di*2, dj*2))) )
                if inBounds(*centPos, M, N):
                    selectionDict[str(i)] = centPos
                    print(f"{i}.", centPos)
                    i += 1
            
            while True:
                selection = input("Number: ")
                if selection in selectionDict.keys():
                    kPos = selectionDict[selection]
                    for DIFF in DIRECTIONS_ALL:
                        neiPos = tuple(map(sum, zip(kPos, DIFF)))
                        if inBounds(*neiPos, M, N) and type(purge.peekCellBase(*neiPos)) == City:
                            purge.map[neiPos[0]][neiPos[1]].noUpdateCnt = 4
                    if inBounds(*kPos, M, N) and type(purge.peekCellBase(*kPos)) == City:
                        purge.map[kPos[0]][kPos[1]].noUpdateCnt = 4
                    break
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(e)
            pass

    def switchPositionWithDoctor(self):
        knightPos = copy.deepcopy(self.root)
        docPos = copy.deepcopy(self.purgeRef.doctor.root)
        self.purgeRef.popFromMap(docPos)
        self.purgeRef.popFromMap(knightPos)
        self.purgeRef.putOnMap(knightPos, self.purgeRef.doctor)
        self.purgeRef.putOnMap(docPos, self)
        self.purgeRef.doctor.root = knightPos
        self.root = docPos        


class Disease(PawnBase):
    def __init__(self, purge: Purge, pos: Tuple[int, int]) -> None:
        super().__init__(purge, pos)

    def growToAdjacent(self) -> None:
        purge = self.purgeRef
        # ◼︎ grow to adjacent
        for i, (dx, dy) in enumerate(DIRECTIONS_ADJ):
            newPos = (self.root[0]+dx, self.root[1]+dy)
            kCell = purge.map[newPos[0]][newPos[1]]
            if isType(purge.peekCell(*newPos), City) and kCell.canBeUpdate:
                purge.putOnMap(newPos, (dis:= Disease(purge, newPos)) )
                purge.diseaseSeeds.append(dis)
                kCell.noUpdateCnt += 5

        # ◼︎ grow to another city
        city: City = purge.searchMapAtPos(City, *self.root)
        if self.root in city.gatePositions:
            newPos = random.choice(city.roadsTo[self.root])[0]
            kCell = purge.map[newPos[0]][newPos[1]]
            if isType(purge.peekCell(*newPos), City) and kCell.canBeUpdate:
                purge.putOnMap(newPos, (dis:= Disease(purge, newPos)) )
                purge.diseaseSeeds.append(dis)
                kCell.noUpdateCnt += 5