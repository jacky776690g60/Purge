import os, sys, argparse, timeit, random, warnings
from typing import *
from Logger import Logger, DebugLevel
from TermArtist import TermArtist
from Purge import Purge
from Utils import PathFinder, DIRECTIONS_ALL, DIRECTIONS_ADJ, inBounds
from Characters import *

def twoplayers():
    purge = Purge(12, 12, 3, 15)
    print("======> Initial Map <======")
    purge.showMap()

    while True:
        try:
            # =============================
            # Doctor
            # =============================
            # ◼︎ movement
            docActionCnt = 1
            while True:
                v = input("(move doctor) w: top, s: south, a: left, d: right, x: sacrifice\n")
                if v in ["w","s","a","d"]:
                    purge.doctor.moveDirectionalByOne(v)
                    purge.showMap()
                    break
                elif v == "x":
                    docActionCnt += 1
                    break
                else:
                    print("unknown command, try again...")
            # ◼︎ action
            while docActionCnt > 0:
                v = input("(Doctor action) cc: cure cross, pn: place nurse: ")
                if v == "cc":
                    purge.doctor.cureCross()
                    purge.showMap()
                    docActionCnt -= 1
                elif v == "pn":
                    purge.doctor.placeNurse()
                    purge.showMap()
                    docActionCnt -= 1
                else:
                    print("unknown command, try again...")
                
                if docActionCnt == 0: break
            
            status = purge.roundEnd(False)
            print("Game Status:", status)
            # print("Disease Seed Count:", len(purge.diseaseSeeds))
            
            if status == 1:
                print("you win!")
                break
            elif status == -1:
                print("you lose!")
                break

            # =============================
            # Kngiht
            # =============================
            # ◼︎ movement
            knightActionCnt = 1
            while knightActionCnt > 0:
                v = input("(move knight) w: top, s: south, a: left, d: right, x: sacrifice\n")
                if v in ["w","s","a","d"]:
                    purge.knight.moveDirectionalByOne(v)
                    purge.showMap()
                    break
                elif v == "x":
                    knightActionCnt += 1
                    break
                else:
                    print("unknown command, try again...")
            # ◼︎ action
            while True:
                v = input("(Knight action) td: throw disinfectant, sw: switch position with doctor: ")
                if v == "td":
                    purge.knight.throwDisinfectant()
                    purge.showMap()
                    knightActionCnt -= 1
                elif v == "sw":
                    purge.knight.switchPositionWithDoctor()
                    purge.showMap()
                    knightActionCnt -= 1
                else:
                    print("unknown command, try again...")

                if knightActionCnt == 0: break


            # ========================================
            # checking game condition and grow disease
            # ========================================
            status = purge.roundEnd()
            print("Game Status:", status)
            # print("Disease Seed Count:", len(purge.diseaseSeeds))
            
            if status == 1:
                print("you win!")
                break
            elif status == -1:
                print("you lose!")
                break

        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(e.with_traceback())


samecitycnt = 0
def ai_knight():
    global samecitycnt

    purge = Purge(10, 10, 2, 5)
    print("======> Initial Map <======")
    purge.showMap()


    while True:
        try:
            # =============================
            # Doctor
            # =============================
            # ◼︎ movement
            docActionCnt = 1
            while True:
                roads = input("(move doctor) w: top, s: south, a: left, d: right, x: sacrifice\n")
                if roads in ["w","s","a","d"]:
                    purge.doctor.moveDirectionalByOne(roads)
                    purge.showMap()
                    break
                elif roads == "x":
                    docActionCnt += 1
                    break
                else:
                    print("unknown command, try again...")
            # ◼︎ action
            while docActionCnt > 0:
                roads = input("(Doctor action) cc: cure cross, pn: place nurse: ")
                if roads == "cc":
                    purge.doctor.cureCross()
                    purge.showMap()
                    docActionCnt -= 1
                elif roads == "pn":
                    purge.doctor.placeNurse()
                    purge.showMap()
                    docActionCnt -= 1
                else:
                    print("unknown command, try again...")
                
                if docActionCnt == 0: break
            
            status = purge.roundEnd(False)
            print("Game Status:", status)
            # print("Disease Seed Count:", len(purge.diseaseSeeds))
            
            if status == 1:
                print("you win!")
                break
            elif status == -1:
                print("you lose!")
                break

            # =============================
            # AI knight
            # =============================
            map, M, N = purge.map, purge.M, purge.N
            knight = purge.knight

            if purge.peekCellBase(*purge.doctor.root) == purge.peekCellBase(*purge.doctor.root):
                print(samecitycnt)
                samecitycnt += 1
                if samecitycnt == 10:
                    knight.switchPositionWithDoctor()
                    samecitycnt = 0

            nearbyDisease = []
            for i in range(1, 3):
                for di, dj in DIRECTIONS_ALL:
                    newPos = (knight.root[0]+di*i, knight.root[1]+dj*i)
                    if not inBounds(*newPos, M, N): continue
                    if isinstance(purge.peekCell(*newPos), Disease):
                        nearbyDisease.append(newPos)
            
            if nearbyDisease:
                targetPos = random.choice(nearbyDisease)
                for DIFF in DIRECTIONS_ALL:
                    neiPos = (targetPos[0]+DIFF[0], targetPos[1]+DIFF[1])
                    if inBounds(*neiPos, M, N) and type(purge.peekCellBase(*neiPos)) == City:
                        purge.map[neiPos[0]][neiPos[1]].noUpdateCnt = 4
                if inBounds(*targetPos, M, N) and type(purge.peekCellBase(*targetPos)) == City:
                    purge.map[targetPos[0]][targetPos[1]].noUpdateCnt = 4
            
            else:
                while True:
                    targetCity = random.choice(purge.cities)
                    if targetCity.edgeDiseases:
                        targetDisease = random.choice(targetCity.edgeDiseases)
                        knight_to_disease = PathFinder.astar(map, knight.root, targetDisease.root, 
                                                            [purge.doctor, *purge.diseaseSeeds, *purge.trees])
                        if knight_to_disease: break
                curCity = purge.peekCellBase(*knight.root)
                print(knight_to_disease)
                if knight_to_disease != -1:
                    isInOtherCity = False
                    for path in knight_to_disease:
                        if purge.peekCellBase(*path):
                            isInOtherCity = True
                            break

                    target_gate_pos = None
                    if isInOtherCity:
                        print("In Another City")
                        for start_gate_pos, roads in curCity.roadsTo.items():
                            for target_gate_path in roads:
                                end_gate_pos = target_gate_path[0]
                                if purge.peekCellBase(*end_gate_pos) == targetCity:
                                    print("End gate:", end_gate_pos)
                                    target_gate_pos = start_gate_pos if not purge.peekCellBase(*knight.root).isGate(*knight.root) else end_gate_pos
                                    break
                    print("Target gate", target_gate_pos)
                    if target_gate_pos:
                        if purge.peekCellBase(*knight.root).isGate(*knight.root):
                            knight.moveTo(target_gate_pos)
                        else:
                            knight_to_disease = PathFinder.astar(map, knight.root, target_gate_pos, 
                                                                [*purge.trees])
                            print(knight_to_disease)
                            knight.moveTo(knight_to_disease[1])
            purge.showMap()

            # ========================================
            # checking game condition and grow disease
            # ========================================
            status = purge.roundEnd()
            print("Game Status:", status)
            # print("Disease Seed Count:", len(purge.diseaseSeeds))
            
            if status == 1:
                print("you win!")
                break
            elif status == -1:
                print("you lose!")
                break

        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(e.with_traceback())



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge")
    parser.add_argument("-ai", "--ai_knight", type=bool, metavar="", default=False,
                        action=argparse.BooleanOptionalAction, help="Start with an AI knight")
    args = parser.parse_args()

    if not args.ai_knight:
        twoplayers()
    elif args.ai_knight:
        ai_knight()