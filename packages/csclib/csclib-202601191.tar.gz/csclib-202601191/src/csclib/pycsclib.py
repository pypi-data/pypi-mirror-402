# from pycsclib import *
#import sys
#import tracemalloc
#import gc
#import csclib
#csclib.start(-1)
#from src.csclib.pycsclib import *

#from ccsclib import Csclib_core, Csclib_bits, Csclib_start
from ccsclib import *
_party = -1

class Share(Csclib_core):
    def typecheck(self, x):
        if not(type(x) is Share):
            raise Exception(x, "is not share")
    def __init__(self, array=None, order=None):
    #    print("Csclib.init")
        super().__init__()
        if array != None:
            if order == None:
                print('order is not given.')
            self.array(array, order)
        return None
    def print(self):
        print('n =', len(self), 'q =', self.order(), ':', self.get())
    def A2B(self, q):
    #    print("A2B")
        tmp = super().A2B(q)
        return Bits()._copy2(tmp)
    def __len__(self):
        return self.len()
    def __add__(self, other):
        if type(other) is int:
            if self.len() != 1:
                print("add: length of self is ", self.len())
            return self.addpublic(0, other)            
        elif type(other) is Share:
            return self.vadd(other)
        elif type(other) is list:
            #tmp = Share(other, self.order()) # addpublic を使うべき
            #return self.vadd(tmp)
            ans = self.dup()
            i = 0
            while i < self.len():
                ans = ans.addpublic(i, other[i]) # 毎回 dup するので非効率
                i += 1
            return ans
        else:
            print("add ???")
            #return self.vadd(other)
    def __radd__(self, other):
        if type(other) is int:
            if self.len() != 1:
                print("add: length of self is ", self.len())
            return self.addpublic(0, other)            
        elif type(other) is Share:
            return self.vadd(other)
        elif type(other) is list:
            #tmp = Share(other, self.order()) # addpublic を使うべき
            #return self.vadd(tmp)
            ans = self.dup()
            i = 0
            while i < self.len():
                ans = ans.addpublic(i, other[i])
                i += 1
            return ans

        else:
            print("radd ???")
            #return self.vadd(other)
    def __sub__(self, other):
        if type(other) is int:
            if self.len() != 1:
                print("sub: length of self is ", self.len())
            return self.addpublic(0, -other)            
        elif type(other) is Share:
            return self.vsub(other)
        elif type(other) is list:
            #tmp = Share(other, self.order()) # addpublic を使うべき
            #return self.vsub(tmp)
            ans = self.dup()
            i = 0
            while i < self.len():
                ans = ans.subpublic(i, other[i])
                i += 1
            return ans
    def __rsub__(self, other):
        if type(other) is int:
            if self.len() != 1:
                print("sub: length of self is ", self.len())
            tmp = self.vneg() # tmp = 1-self
            return tmp.addpublic(0, other-1) # 1-self + other-1 = other-self
        elif type(other) is list:
            #tmp = Share(other, self.order()) # addpublic を使うべき
            #return tmp.vsub(self)
            ans = self.vneg()
            i = 0
            while i < self.len():
                ans = ans.addpublic(i, other[i]-1) # 正しい?
                i += 1
            return ans
        else:
            print("rsub ???")
            #return other.vsub(self)
    def __mul__(self, other):
        if type(other) is int:
            return self.smul(other)
        elif type(other) is Share:
            return self.vmul(other)
        elif type(other) is list:
            tmp = Share(other, self.order())
            return self.vmul(tmp)
        else:
            print("mul ???")
            #return self.vmul(other)
    def __rmul__(self, other):
        if type(other) is int:
            return self.smul(other)
        elif type(other) is Share:
            return self.vmul(other)
        elif type(other) is list:
            tmp = Share(other, self.order())
            return tmp.vmul(other)
        else:
            print("rmul ???")
            #return self.vmul(other)
    def __matmul__(self, other): # a @ b
        if type(other) is int:
            return self.insert_tail(other)
        elif type(other) is Share:
            return self.concat(other)
        elif type(other) is list:
            tmp = Share(other, self.order())
            return self.concat(tmp)
        else:
            print("@ ???")
            #return self.concat(other)
    def __rmatmul__(self, other): # a @ b
        if type(other) is int:
            return self.insert_head(other)
        elif type(other) is list:
            tmp = Share(other, self.order())
            return tmp.concat(self)
        else:
            print("rmatmul ???")
#    def __pow__(self, other): # a ** 0
#        return self.insert_tail(other)
#    def __rpow__(self, other): # 0 ** a
#        return self.insert_head(other)
############################################
# 論理演算
# 入力は 0, 1 のみ
############################################
    def __invert__(self): # ~a
        return self.vneg()
    def __and__(self, other): # a & b
        return self.vmul(other)
    def __or__(self, other): # a | b
        ap = self.vneg()
        bp = other.vneg()
        c = ap.vmul(bp)
        return c.vneg()
    def __xor__(self, other): # a ^ b
        a = self.vadd(other)
        c = self.vmul(other)
        d = c.smul(2)
        ans = a.vsub(d)
        return ans
############################################
# 比較
    def __eq__(self, other):
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
        #    self2 = self.A2B(self.order())
        #    other2 = other.A2B(self.order())
            return self2 == other2
        else:
            return self.eq(other)
    def __ne__(self, other):
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
            return self2 != other2
        else:
            return self.eq(other).vneg()
    def __lt__(self, other):
    #    print("Share lt")
        if type(other) is int:
            other = Share([other], self.order())
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
            return self2 < other2
        else:
            return self.lt(other)
    def __ge__(self, other):
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
            return self2 >= other2
        else:
            return self.lt(other).vneg()
    def __gt__(self, other):
    #    print("Share gt")
    #    print("self")
    #    self.print()
    #    print("other")
    #    other.print()
        if type(other) is int:
            other = Share([other], self.order())
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
        #    self2 = self.A2B(self.order())
        #    other2 = other.A2B(self.order())
            return self2 > other2
        else:
            return other.lt(self)
    def __le__(self, other):
        if self.order() != 2 or other.order() != 2:
            self2 = self.A2B(2)
            other2 = other.A2B(2)
            return self2 <= other2
        else:
            return other.lt(self).vneg()
    def __bool__(self):
        if self.len() != 1:
            print("bool: length of self is ", self.len())
        c0 = self.reconstruct()
#        print("bool c0")
#        c0.print()
        c1 = c0.get()
        c = c1[0]
        return c == 1
    
############################################
    def __getitem__(self, index):
        #print('slice', index, type(index))
        if type(index) is int:
            return self.slice(index, index+1)
        elif type(index) is slice:
            start = index.start
            end = index.stop
            #print('start', start, 'end', end, 'step', index.step)
            if start == None:
                start = 0
            if end == None:
                end = 0
            return self.slice(start, end)
        else:
            print("getitem?")
    def __setitem__(self, index, x):
        if type(index) is int: # a[i] = x
            if type(x) is int: # 公開値
                return self.setpublic(index, x)
            else:
                if x.len() != 1:
                    print("setitem: length of x is ", x.len())
                return self.setshare(index, x, 0)
        elif type(index) is slice: # a[s:e] = x
            start = index.start
            end = index.stop
            if type(x) is int: # 公開値
            #    return self.setpublic(start, x) # うそ
                i = start
                while i < end:
                    self.setpublic(i, x)
                    i += 1
                return self
            else:
                if start == None:
                    start = 0
                if end == None:
                    end = len(self)
                return self.setshares(start, end, x, 0)
    def sort(self):
        return radix_sort(self)
##############################################
# Share の定義おわり
##############################################

class Bits(Csclib_bits):
    def typecheck(self, x):
        if not(type(x) is Bits):
            raise Exception(x, "is not bit share")
    def __init__(self, array=None, order=None, order2=None):
        #print("Bits(Csclib_bits) init")
        super().__init__()
        if array != None:
            if order == None or order2 == None:
                print('order is not given.')
            tmp = Share().array(array, order)
            tmp2 = tmp.A2B(order2) # order2 は変換後の各桁の位数
            self._copy2(tmp2)
        return None
    def print(self):
        tmp = super().get()
        i = 0
        for x in tmp:
            print('i =', i, end=" ")
            Share()._copy(x).print()
            i += 1
    def get(self):
        tmp = super().get()
        ans = []
        for x in tmp:
            ans.append(Share()._copy(x))
        return ans
    def new(self, list):
        tmp = super().set(list)
        return Bits()._copy(tmp)
    def __pow__(self, other): # X ** Y (下位ビットが X, 上位ビットが Y)
        return Bits().new(self.get() + other.get())
    def __len__(self):
        return self.len()
    def B2A(self):
        tmp = super().B2A()
        return Share()._copy(tmp)
    def __getitem__(self, index):
        #print('slice', index, type(index))
        if type(index) is int:
            return self.slice(index, index+1) 
        elif type(index) is slice:
            start = index.start
            end = index.stop
            #print('start', start, 'end', end, 'step', index.step)
            if start == None:
                start = 0
            if end == None:
                end = 0
            return self.slice(start, end)
        else:
            print("getitem?")
    def __setitem__(self, index, x):
        if type(index) is int: # a[i] = x
            if type(x) is int: # 公開値
                return self.setpublic(index, x)
            else:
                if x.len() != 1:
                    print("setitem: length of x is ", x.len())
                return self.setshare(index, x, 0)
        elif type(index) is slice: # a[s:e] = x
            start = index.start
            end = index.stop
            if type(x) is int: # 公開値
                i = start
                while i < end:
                    self.setpublic(i, x)
                    i += 1
                return self
        else:
            print("setitem?")
############################################
# 比較
    def __eq__(self, other):
        tmp = super().eq(other)
        return Share()._copy(tmp)
    def __ne__(self, other):
        tmp = super().eq(other)
        return Share()._copy(tmp.vneg())
    def __lt__(self, other):
    #    print("Bits lt")
    #    print("self")
    #    self.print()
    #    print("other")
    #    other.print()
        tmp = super().lt(other)
        return Share()._copy(tmp)
    def __ge__(self, other):
        tmp = super().lt(other)
        return Share()._copy(tmp.vneg())
    def __gt__(self, other):
#        print("Bits gt")
#        print("other")
#        other.print()
#        print("self")
#        self.print()
        tmp = other.lt(self)
        return Share()._copy(tmp)
    def __le__(self, other):
        tmp = other.lt(self)
        return Share()._copy(tmp.vneg())
    def sort(self):
        return radix_sort_bits(self)

##############################################
# Bits の定義おわり
##############################################

############################################
# 整数の桁数を求める
# to store an integer in [0,x-1], we need blog(x-1)+1 bits
############################################
def blog(x):
    l = -1
    while x > 0:
        x >>= 1
        l += 1
    return l

################################
# x を下位 low ビットとそれ以外に分ける
################################
def partition(x, low):
    q = x.order()
    B = x.A2B(2).get()
    R = B[:low] # 下位
    Q = B[low:] # 上位
    i = 0
    while i < len(R):
        R[i] = R[i].extend(1<<low)
        i += 1
    i = 0
    while i < len(Q):
        Q[i] = Q[i].extend(q)
        i += 1
    rb = Bits().new(R)
    qb = Bits().new(Q)

    L = rb.B2A()
    H = qb.B2A()
    return (H, L)

def PrefixSum(v):
    n = len(v)
    if v.order() < n+1:
        k2 = blog(n+1-1)+1
        v = v.extend(1<<k2)
#    ans = v.dup()
#    sum = 0
#    i = 0
#    while i < n:
#        sum += v[i]
#        ans[i] = sum
#        i += 1
    ans = v.PrefixSum()
    return ans

def SuffixSum(v):
    n = len(v)
    if v.order() < n+1:
        k2 = blog(n+1-1)+1
        v = v.extend(1<<k2)
#    ans = v.dup()
#    sum = 0
#    i = n-1
#    while i >= 0:
#        sum += v[i]
#        ans[i] = sum
#        i -= 1
    ans = v.SuffixSum()
    return ans

def Diff(v, z):
    n = len(v)
#    ans = v.dup()
#    prev = z
#    i = 0
#    while i < n:
#        ans[i] = v[i] - prev
#        prev = v[i]
#    return ans
    return v.Diff(z)

def rank1(v):
    n = len(v)
    if v.order() < n+1:
        k2 = blog(n+1-1)+1
        v = v.extend(1<<k2)
#    ans = v.dup()
#    sum = 0
#    i = 0
#    while i < n:
#        sum += v[i]
#        ans[i] = sum
#        i += 1
    ans = v.rank1()
    return ans

def rank0(v):
    n = len(v)
    if v.order() < n+1:
        k2 = blog(n+1-1)+1
        v = v.extend(1<<k2)
#    ans = v.dup()
#    sum = 0
#    i = 0
#    while i < n:
#        sum += 1 - v[i]
#        ans[i] = sum
#        i += 1
    ans = v.rank0()
    return ans

def Sum(v):
    n = len(v)
    if v.order() < n+1:
        k2 = blog(n+1-1)+1
        v = v.extend(1<<k2)
#    ans = v[0]
#    i = 1
#    while i < n:
#        ans[0] += v[i]
#        i += 1
    ans = v.sum()
    return ans

def rshift(v, z):
#    n = len(v)
#    ans = v.dup()
#    ans = Share().const(n, 0, v.order())
#    ans.setshares(0, n, v, 0)
#    ans.setshares(1, n, v, 0)
#    ans[0] = v.public(z)
#    ans.setpublic(0, z)
#    ans = v.public(z) ** v[:-1]
#    ans = v.public(z) @ v[:-1]
    ans = z @ v[:-1]
    return ans

def lshift(v, z):
#    n = len(v)
#    ans = v.dup()
#    ans.setshares(0, n-1, v, 1)
#    ans[n-1] = v.public(z)
#    ans = v[1:] ** v.public(z)
#    ans = v[1:] @ v.public(z)
    ans = v[1:] @ z
    return ans

def rrotate(v):
    n = len(v)
#    ans = v.dup()
#    ans.setshares(1, n, v, 0)
#    ans[0] = v[n-1]
#    ans = v[n-1] ** v[:-1]
    ans = v[n-1] @ v[:-1]
    return ans

def lrotate(v):
    n = len(v)
#    ans = v.dup()
#    ans.setshares(0, n-1, v, 1)
#    ans[n-1] = v[0]
#    ans = v[1:] ** v[0]
    ans = v[1:] @ v[0]
    return ans

def IfThenElse(f, a, b):
    if f.order() < a.order():
        f = f.extend(a.order())
    n = len(f)
    if n !=len(a) or n != len(b):
        print("IfThenElse f->n =", n, "a->n = ", len(a), "b->n = ", len(b))
    ans = (a - b)*f + b
    return ans

def StableSort(g):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    return g.StableSort()
#    print("g")
#    g.print()
    n = len(g)
    r0 = rank0(g)
#    print("r0")
#    r0.print()
    r1 = rank1(g)
#    print("r1")
#    r1.print()
    s0 = rshift(r0, 0)
#    print("s0")
#    s0.print()
    s1 = rshift(r1, 0)
#    print("s1")
#    s1.print()
#    s = r0[n-1]
#    i = 0
#    while i < n:
#        s1[i] += s
#        i += 1
    s1.addall(r0[n-1])
#    print("s1")
#    s1.print()
    sigma = IfThenElse(g, s1, s0)
#    print("sigma")
#    sigma.print()
    return sigma


def Perm_ID(v):
    n = len(v)
    ans = v.dup()
#    i = 0
#    while i < n:
#        ans[i] = i
#        i += 1
    ans.setperm()
    return ans

def Perm_ID2(n, q):
    w = blog(q-1)+1
    ans = Share().const(n, 0, 1<<w)
    return Perm_ID(ans)

def InvPerm(sigma):
    perm = Perm_ID(sigma)
    ans = perm.AppInvPerm(sigma)
    return ans


def GenCycle(g):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    return g.GenCycle()
    n = len(g)
    sigma = StableSort(g)
    perm = Perm_ID(g)
    gneg = ~g
    t0 = perm * gneg
    t1 = perm * g
    u = t1.AppInvPerm(sigma)
    v = lshift(u, 0)
    y = v.AppPerm(sigma)
    pi = y + t0
    w = rshift(u, 0)
    z = w.AppPerm(sigma)
    pi_inv = z + t0
    pi_inv[0] = u[n-1]
    return (pi, pi_inv)

def Propagate(g, v):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    (pi, tmp_y) = GenCycle(g)
#    print("pi")
#    pi.print()
#    print("tmp_y")
#    tmp_y.print()

    x = v.AppInvPerm(pi)
#    print("x0")
#    x.print()
    x[0] = 0
#    print("x1")
#    x.print()
    v2 = v - x
 #   print("v2")
 #   v2.print()
    z = PrefixSum(v2)
 #   print("z")
 #   z.print()
    return z

def GroupSum(g, v):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    (tmp_x, pi_inv) = GenCycle(g)
    s = SuffixSum(v)
    t = s.dup()
    t[0] = 0
    y = t.AppInvPerm(pi_inv)
    s = s - y
    return s

def select1(g):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    return g.select1()
    n = len(g)
    s0 = rank0(g)
    s0 = rshift(s0, 0)
    m = sum(g)
#    i = 0
#    while i < n:
#        s0[i] += m[0]
#        i += 1
    s0.addall(m)
    s1 = rank1(g)
    s1 = rshift(s1, 0)
    sigma = IfThenElse(g, s1, s0)
    gneg = ~g
    t0 = n * gneg
    t1 = g.dup()
    i = 0
    while i < n:
        t1[i] = t1[i] * i ############################# 要改良
        i += 1
    t = t0 + t1
    u = t.AppInvPerm(sigma)
    return u

def select0(v):
    if g.order() < g.len():
        k2 = blog(g.len()-1)+1
        g = g.extend(1<<k2)
    return g.select0()
    return select1(~v)

def radix_sort(a_):
    a = a_.dup()
    w = blog(len(a)-1)+1
    pi = Perm_ID2(len(a), 1 << w)
    q = a.order()
    qb = 1 << w
    k = 1
    while k < q:
#        print("k ", k)
#        (tmp_x, tmp_y) = a.A2QB(q//k, 2)
        (tmp_x, tmp_y) = a.A2QB(q//k, q)
        sigma = StableSort(tmp_y)
        if tmp_x.order() > 1:
            a = tmp_x.AppInvPerm(sigma)
        pi = pi.AppInvPerm(sigma)
        k *= 2
    x = a_.AppPerm(pi)
    return (x, pi)


def radix_sort_bits(a):
    d = a.depth()
 #   print("a", a)
    A = a.get()
 #   print("A", A)
    pi = StableSort(A[0])
    k = 1
    while k < d:
        ap = A[k].AppInvPerm(pi)
        sigma = StableSort(ap)
        pi = sigma.AppPerm(pi)
        k += 1
    return pi


def Grouping_bit(V):
    Vp = rshift(V, 1)
    Vp[0] -= V[0]
    ans = ~(V == Vp)
    return ans

def Grouping_bits(V):
    B = V.get()
    d = len(B)
    b = Grouping_bit(B[0])
    i = 1
    while i < d:
        g = Grouping_bit(B[i])
        b = b | g
        i += 1
    return b

def Propagate_bits(g, V):
#    print("g")
#    g.print()
    B = V.get()
    ans = []
    for b in B:
#        print("b")
#        b.print()
#        print("tmp")
        tmp = Propagate(g, b)
#        tmp.print()
        ans.append(Propagate(g, b))
    return Bits().new(ans)

def Grouping_name(L, q):
    V = Share([0] * L.len(), q)
#    i = 0
#    while i < V.len():
#        V[i] = i
#        i += 1
    V.setperm()
    return Propagate(L, V)


def BatchAccessUnary(v, idx):
    U = len(v)
    N = len(idx)
    sigma = StableSort(idx)
#    n = Sum(idx)
    zeros = Share([0]*(N-U), v.order())
    X = v @ zeros
    Y = X.AppPerm(sigma)
    nidx = ~idx
    Z = Propagate(nidx, Y)
    W = Z.AppInvPerm(sigma)
    ans = W[U:N] # W[U:]
    return ans
