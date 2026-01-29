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
  elif len(args) >= 2:
    fname = args[1]

  print('party ', party)
  Csclib_start(party)


  rB = [0,1,0,0,1,1,0,0,1,0,0,0,0,1,0,0]
  q = len(rB)*2
  B = Share(rB, q)

  n = len(B)
  m = Sum(B).reconstruct().get()[0]
  print(n, m)

  w = blog(n-1)+1
  z = blog(m)
  print(w, z)

  s1 = select1(B)[:m]
  s1.print()

#  sb = s1.A2B(2).get()
#  R = sb[:w-z]
#  Q = sb[w-z:]
#  i = 0
#  while i < len(R):
#    R[i] = R[i].extend(1<<(w-z))
#    i += 1
#  i = 0
#  while i < len(Q):
#    Q[i] = Q[i].extend(1<<z)
#    i += 1
#  rb = Bits().new(R)
#  qb = Bits().new(Q)
#
#  L = rb.B2A()
#  q = qb.B2A()
  (Q, L) = partition(s1, w-z)
  L.print()
  Q.print()

  U = Q.Unary(1<<z)
  H = U.A2QB(1<<z, 2)[1]
  H.print()
  L.print()
