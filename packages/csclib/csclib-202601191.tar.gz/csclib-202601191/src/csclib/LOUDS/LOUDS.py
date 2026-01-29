from csclib import *

def LOUDS_parent(b):
    n = len(b)
    p = rank1(b)
    sigma = StableSort(b)
    v = p.AppInvPerm(sigma)
    parent = v[0:n//2]
    i = 0
    while i < len(parent):
        parent[i] += -1
        i += 1
    return parent

def LOUDS_firstchild(bb):
    b = bb[1:]
    n = len(b)
    Q = rank0(b)
    sigma = StableSort(b)
    v = Q.AppInvPerm(sigma)
    firstchild = v[n//2: n]
    i = 0
    while i < len(firstchild):
        firstchild[i] += 1
        i += 1
    return firstchild

def LOUDS_contract(b_):
    b = b_[1:]
    n = len(b)
    p = rank1(b)
    q = rank0(b)
    sigma = StableSort(b)
    r = IfThenElse(b, q, p)
    v0 = r.AppInvPerm(sigma)
    v1 = v0.dup()
    v1[0:(n//2)-1] = v0[(n//2)+1:(n//2)*2]
    v1[(n//2)-1] = n//2
    v1[n//2:(n//2)*2+1] = v0[0:(n//2)+1]
    v  = v1.AppPerm(sigma)
    d1 = Propagate(~b, v)
    d1 -= r
    b1 = 1 @ b
    zv = 0 @ v
    d0 = Propagate(b1, zv)
    d0 = d0[1:]
    d0 -= r
    d = IfThenElse(b, d1, d0)
    perm = Perm_ID(b)
    pi = d + perm
    bb = 1 @ b.AppInvPerm(pi)
    return (bb, pi)

def LOUDS_grandparent(b):
    parent = LOUDS_parent(b)
    bb = b[1:]
    bneg = ~bb
    bneg = bneg[1:]
    p2 = 0 @ BatchAccessUnary(parent, bneg)
    return p2

def LOUDS_grandchild(b):
    n = len(b)//2
    firstchild = LOUDS_firstchild(b) @ (n+1)
    c2 = BatchAccessUnary(firstchild, 0 @ b)
    c2 = c2[1:]
    return c2

def select0_from_parent(parent):
    n = len(parent)
    pi = parent.dup()
    i = 0
    while i < n:
        pi[i] += i+1
    return pi

def select1_from_child(firstchild):
    n = len(firstchild)
    pi = firstchild.dup()
    i = 0
    while i < n:
        pi[i] += i
    return 0 @ pi

def ArrayToLOUDS(parent, firstchild):
    n = len(parent)
    pi1 = select0_from_parent(parent)
    pi2 = select1_from_child(firstchild)
    pi = pi1 @ pi2
    b = Share([0]*n + [1]*(n+1), parent.order())
    L = b.AppInvPerm(pi)
    return (L, pi)

def LOUDS_contract_supereasy(b):
    p2 = LOUDS_grandparent(b)
    c2 = LOUDS_grandchild(b)
    (L, pi) = ArrayToLOUDS(p2, c2)
    return L

def LOUDS_PathSum(b, w):
    n = len(b)//2
    b0 = b.dup()
    bb1 = b0[1:]
    sigma = StableSort(bb1)
    w2 = w @ w
    s0 = 0 @ w2.AppPerm(sigma)
    r = 1
    while r <= n:
        sigma0 = StableSort(b0)
        d0 = Propagate(b0, s0)
        s0 += d0
        e1 = s0.AppInvPerm(sigma0)
        (b1, rho0) = LOUDS_contract(b0)
        ztmp = e1[0:n]
        z1 = ztmp @ 0
        z1 = z1 @ ztmp
        c1 = z1.AppPerm(sigma0)
        c1 = c1[1:]
        s1 = c1.AppInvPerm(rho0)
        r = r*2
        b0 = b1
        s0 = 0 @ s1
    ans = z1[0:n]
    return ans

def LOUDS_get_parent(w, b_):
    b = b_[1:]
    b = 0 @ b
    b = 1 @ b
    I = ~b
    wp = BatchAccessUnary(w, I)
    return wp

def LOUDS_PathSum_supereasy(b_, w_):
    b = b_.dup()
    w = 0 @ w_
    n = len(w)
    d = 1
    while d < n:
        wp = LOUDS_get_parent(w, b)
        w += wp
        b = LOUDS_contract_supereasy(b)
        d = d*2
    w = w[1:]
    return w

def LOUDS_TreeSum(b, w):
    bb = b[1:]
    sigma = StableSort(bb)
    w2 = w @ w
    wb = w2.AppPerm(sigma)
    n = len(b)//2
    b0 = bb
    s0 = wb
    r = 1
    while r <= n:
        sigma0 = StableSort(b0)
        p0 = SuffixSum(s0)
        e1 = p0.AppInvPerm(sigma0)
        z20 = e1[n:]
        z21 = e1[n+1:] @ 0
        z2 = z20 - z21
        z1 = z2 @ z2
        b01 = 1 @ b0
        (b1, rho0) = LOUDS_contract(b01)
        c1 = z1.AppPerm(sigma0)
        s1 = c1.AppInvPerm(rho0)
        r = r*2
        b0 = b1[1:]
        s0 = s1
    ans = z1[0:n]
    return ans

def LOUDS_Distribute(wp, wc, b):
    sigma = StableSort(b)
    ww = wc @ wp
    wb = ww.AppPerm(sigma)
    return wb

def LOUDS_Duplicate(w, b):
    return LOUDS_Distribute(w, w, b)

def LOUDS_gather(wb, b):
    n = len(b)//2
    sigma0 = StableSort(b)
    e1 = wb.AppInvPerm(sigma0)
    e1 = e1[n:]
    return e1

def LOUDS_TreeSum_easy(b, w):
    bb = b[1:]
    wb = LOUDS_Duplicate(w, bb)
    n = len(b)//2
    b0 = bb
    s0 = wb
    r = 1
    while r <= n:
        p0 = SuffixSum(s0)
        e1 = LOUDS_gather(p0, b0)
        e10 = lshift(e1,0)
        z2 = e1 - e10
        r = r*2
        if r > n:
            break
        b01 = 1 @ b0
        (b1, tmp) = LOUDS_contract(b01)
        b0 = b1[1:]
        s0 = LOUDS_Duplicate(z2, b0)
    return z2

def LOUDS_sum_children(wc, b):
    n = len(b)//2
    sigma = StableSort(b)
    wc0 = wc @ ([0]*n)
    wb = wc0.AppPerm(sigma)
    s = SuffixSum(wb)
    e = LOUDS_gather(s, b)
    e0 = lshift(e, 0)
    z = e - e0
    return z

def LOUDS_TreeSum_supereasy(b_, w_):
    n = len(b_)//2
    r = 1
    b = b_.dup()
    w = w_.dup()
    while r <= n:
        b1 = b[1:]
        wc = LOUDS_sum_children(w, b1)
        w += wc
        (b, tmp) = LOUDS_contract(b)
        r = r*2
    return w

def LOUDS_depth(b):
    n = len(b)//2
    w = Share([1]*n, b.order())
    ans = LOUDS_PathSum(b, w)
    return ans

def LOUDS_treesize(b):
    n = len(b)//2
    w = Share([1]*n, b.order())
    ans = LOUDS_TreeSum(b, w)
    return ans

def LOUDS_ancestors(b):
    n = len(b)//2
    w = Share([0]*n, b.order())
    w = _const(n, 0, order(b))
    i = 0
    while i < n:
        w[i] = i+1
    ans = LOUDS_PathSum(b, w)
    return ans

def LOUDS_degree(b):
    n = len(b)//2
    wc = Share([1]*n, b.order())
    ans = LOUDS_sum_children(wc, b)
    return ans

def LOUDS_prerank(bb):
    n = len(bb)//2
    b = bb[1:]
    sigma = StableSort(b)
    d = LOUDS_depth(bb)
    e = d[1:]
    e2 = d[:-1]
    e -= e2
    e = 1 @ e
    f = e.dup()
    s = LOUDS_treesize(bb)
    f0 = Share([0]*n, e.order())
    f0 = f0 @ f
    f0 = f0 @ e
    f1 = f0.AppPerm(sigma) # 各レベルの最初の位置
    s1 = Share([0]*n, s.order())
    s2 = s @ s1
    s0 = s2.AppPerm(sigma)
    bs = PrefixSum(~b) # 子の ID
    zeros = Share([0]*(n*2), bs.order())
    h1 = IfThenElse(f1, bs, zeros) # 各レベルの最後のノードの ID
    p = PrefixSum(s0)
    f1 = 1 @ f1
    p0 = p - h1
    p0 = 0 @ p0
    pp = Propagate(f1, p0)
    pp = pp[1:]
    q = p - pp
    q = q - s0
    q = q - PrefixSum(h1)
    x = q.AppInvPerm(sigma)
    x = x[0:n]
    a = LOUDS_ancestors(bb)
    z = x + a
    z = z - Perm_ID(z)
    return z

def LOUDS_to_BP(bb):
    n = len(bb)//2
    b = bb[1:]
    sigma = StableSort(b)
    d = LOUDS_depth(bb)
    s = LOUDS_treesize(bb)
    z = LOUDS_prerank(bb)
    v = z * 2
    c = Share([1]*n, v.order())
    v = v - c
    v = v - d #  開き括弧の位置
    w = s * 2
    w = w - c
    w = w + v #  閉じ括弧の位置
    vw = v @ w
    pi = vw.AppPerm(sigma)
    bp = b.AppInvPerm(pi)
    return (bp, pi)

def BP_to_LOUDS(BP):
    OP = 0
    CP = 1
    n = len(BP)
    k = blog(n-1)+1
    P = BP.extend(1<<k)
#    print('P0')
#    P.print()
    P = -2 * P
#    print('P0')
#    P.print()
    i = 0
    while i < n:
        P[i] += 1
        i += 1
#    print('P1')
#    P.print()
    D = 0 @ PrefixSum(P)
    BP0 = OP @ BP

#    print('D')
#    D.print()
    (tmp, sigma) = radix_sort(D)
    print('sigma')
    sigma.print()
    LOUDS = BP0.AppPerm(sigma)
    LOUDS = ~LOUDS
    ans = (LOUDS, sigma)
    return ans

def BP_to_share(BP):
    OP = 0
    CP = 1
    n = len(BP)
    s = Share([0]*n, 2)
    i = 0
    while i < n:
        if BP[i] == '(':
            c = OP
        elif BP[i] == ')':
            c = CP
        else:
            print('BP[', i, '] = ', BP[i])
            return None
        s[i] = c
        i += 1
    return s
