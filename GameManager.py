import os, sys, argparse, timeit, random, warnings
from typing import *
from Logger import Logger, DebugLevel
from TermArtist import TermArtist
from Purge import Purge

def actualGame():
    purge = Purge(10, 10, 2, 8)
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
            print("Disease Seed Count:", len(purge.diseaseSeeds))
            
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
    actualGame()