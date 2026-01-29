import sys
import random
from csclib import *



if __name__ == '__main__':
  party = -1

  args = sys.argv
  if len(args) >= 2:
    party = int(args[1])

  print('party ', party)
  Csclib_start(party)

  str = "tobeornottobe"
  T = []
  for c in str:
    T.append(ord(c))
  sT = Share(T, 256)
#  (I, LCP) = SuffixSort_LCP(sT)
#  print("I ")
#  I.print()
#  print("LCP ")
#  LCP.print()
  SuffixSort_DC3(sT)
