def blog(x):
    l = -1
    while x > 0:
        x >>= 1
        l += 1
    return l

def dup(v):
  n = len(v)
  ans = [0] * n
  i = 0
  while i < n:
    ans[i] = v[i]
    i += 1
  return ans

def Sum(v):
    n = len(v)
    ans = v[0]
    i = 1
    while i < n:
        ans += v[i]
        i += 1
    return ans

def rank0(v):
    n = len(v)
    ans = [0] * n
    sum = 0
    i = 0
    while i < n:
        sum += 1 - v[i]
        ans[i] = sum
        i += 1
    return ans

def rank1(v):
    n = len(v)
    ans = [0] * n
    sum = 0
    i = 0
    while i < n:
        sum += v[i]
        ans[i] = sum
        i += 1
    return ans

def rshift(v, z):
    n = len(v)
    ans = [z] + v[:-1]
    return ans

def vneg(v):
  n = len(v)
  i = 0
  ans = [0] * n
  while i < n:
    ans[i] = 1 - v[i]
    i += 1
  return ans

def IfThenElse(f, a, b):
    n = len(f)
    i = 0
    ans = [0] * n
    while i < n:
      ans[i] = (a[i] - b[i]) * f[i] + b[i]
      i += 1
    return ans

def vadd(x, y):
  n = len(x)
  ans = [0] * n
  i = 0
  while i < n:
    ans[i] = x[i] + y[i]
    i += 1
  return ans

def select1(g):
    n = len(g)
    s0 = rank0(g)
    s0 = rshift(s0, 0)
    m = Sum(g)
    i = 0
    while i < n:
        s0[i] += m
        i += 1
    s1 = rank1(g)
    s1 = rshift(s1, 0)
    sigma = IfThenElse(g, s1, s0)
    gneg = vneg(g)
#    t0 = n * gneg
    t0 = [0] * n
    i = 0
    while i < n:
      t0[i] = gneg[i] * n
      i += 1
    t1 = dup(g)
    i = 0
    while i < n:
        t1[i] = t1[i] * i
        i += 1
    t = vadd(t0, t1)
    u = t.AppInvPerm(sigma)
    return u


if __name__ == '__main__':

  B = [0,1,0,0,1,1,0,0,1,0,0,0,0,1,0,0]

  n = len(B)
  m = Sum(B)[0]
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
