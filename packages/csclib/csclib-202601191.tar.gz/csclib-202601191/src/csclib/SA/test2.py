import sys
import random
import time
from csclib import *



if __name__ == '__main__':
  party = -1

  args = sys.argv
  if len(args) >= 3:
    party = int(args[1])
    fname = args[2]
  else:
    fname = args[1]

  print('party ', party)
  Csclib_start(party)

#  str = "tobeornottobe"
#  str = "tobeorno"
#  str = "tobeornottob"
  f = open(fname, 'r')
  str = f.read()
  f.close()

  T = []
  for c in str:
    T.append(ord(c))
  sT = Share(T, 256)
#  (I, LCP) = SuffixSort_LCP(sT)
#  print("I ")
#  I.print()
#  print("LCP ")
#  LCP.print()

  time_start = time.time()
  SA = SuffixSort(sT)
  time_end = time.time()
  lap = time_end- time_start
  print('SuffixSort    time ', lap)

  time_start = time.time()
  SAd = SuffixSort_DC3(sT)
  time_end = time.time()
  lap = time_end- time_start
  print('SuffixSortDC3 time ', lap)

  SA0 = SA.get()
  SAd0 = SAd.get()
  print(SA0 == SAd0)
#  print('SA0 ', SA0)
#  print('SAd0 ', SAd0)
#  Suffix_print(T, SA0)
