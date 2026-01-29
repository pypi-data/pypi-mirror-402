from csclib import *

def SuffixSort(T):
    #print("T")
    #T.print()
    n = len(T)
    d = blog(n+1-1)+1
#    allone = Share([1]*n, T.order())
    allone = Share().const(n, 1, T.order())
    V = T + allone
    V = V @ 0
    Vb = V.A2B(1<<d) # T をビット分解する
#    Vb = V.A2B(T.order()) # T をビット分解する
#    J = radix_sort_bits(Vb) #  1文字でのソートを表す置換
    J = Vb.sort() #  1文字でのソートを表す置換
#    print('J')
#    J.print()
    W = Vb.AppInvPerm(J) # 1文字のソート結果 (pos -> lex)
#    print('W')
#    W.print()
    L = Grouping_bits(W) # グループの境界を求める

#    Va = Bits([0]*(n+1), 1<<d, 1<<d)
#    i = 0
#    while i < n+1:
#        Va[i] = i
#        i += 1
#    Va = Propagate_bits(L, Va)
    Va = Grouping_name(L, 1<<d)
    Va = Va.A2B(1<<d)

    h = 1
    s = Sum(L)
    while h < n:
    #    print("h", h)
        V1 = Va.AppPerm(J)
    #    J2 = Share().const(n+1, 0, 1<<d)
#        J2 = Share([0]*(n+1), 1<<d)
#        i = 0
#        while i < n+1:
#            J2[i] = J[(i+h) % (n+1)]
#            i += 1
        J2 = J[h:] @ J[:h]
        V2 = Va.AppPerm(J2)
        #tmp = V2.get() + V1.get()
        #Vb = Bits().new(tmp)
        Vb = V2 ** V1
    #    J = radix_sort_bits(Vb)
        J = Vb.sort()
        W = Vb.AppInvPerm(J)
        L = Grouping_bits(W)
#        i = 0
#        while i < n+1:
#            Va[i] = i
#            i += 1
#        Va = Propagate_bits(L, Va)
        Va = Grouping_name(L, 1<<d)
        Va = Va.A2B(1<<d)


        h = h*2
        s = Sum(L)
        print("s")
        s.print()
#        sn = Share([n], s.order())
#        c = (s > sn)
#        c = (s > n)
#        c.print()
#        if bool(s > sn):
        if bool(s > n):
#            print("break")
            break
#    print("J")
#    J.print()
    I = InvPerm(J)
#    print("I")
#    I.print()
    return I

def SuffixSort_LCP(T):
    #print("T")
    #T.print()
    n = len(T)
    d = blog(n+1-1)+1
#    allone = Share().const(n, 1, T.order())
    allone = Share([1]*n, T.order())
    V = T + allone
    V = V @ 0
    Vb = V.A2B(1<<d) # T をビット分解する
#    J = radix_sort_bits(Vb) #  1文字でのソートを表す置換
    J = Vb.sort() #  1文字でのソートを表す置換
    W = Vb.AppInvPerm(J) # 1文字のソート結果 (pos -> lex)
    L = Grouping_bits(W) # グループの境界を求める
#    Va = Bits([0]*(n+1), 1<<d, 1<<d)
#    i = 0
#    while i < n+1:
#        Va[i] = i
#        i += 1
#    Va = Propagate_bits(L, Va)
    Va = Grouping_name(L, 1<<d)
    Va = Va.A2B(1<<d)

    VV = []
    VV.append(Va.dup())

    h = 1
    s = Sum(L)
    while h < n:
    #    print("h", h)
        V1 = Va.AppPerm(J)
    #    J2 = Share().const(n+1, 0, 1<<d)
#        J2 = Share([0]*(n+1), 1<<d)
#        i = 0
#        while i < n+1:
#            J2[i] = J[(i+h) % (n+1)]
#            i += 1
        J2 = J[h:] @ J[:h]
        V2 = Va.AppPerm(J2)
#        tmp = V2.get() + V1.get()
#        Vb = Bits().new(tmp)
        Vb = V2 ** V1
#        J = radix_sort_bits(Vb)
        J = Vb.sort()
        W = Vb.AppInvPerm(J)
        L = Grouping_bits(W)
#        i = 0
#        while i < n+1:
#            Va[i] = i
#            i += 1
#        Va = Propagate_bits(L, Va)
        Va = Grouping_name(L, 1<<d)
        Va = Va.A2B(1<<d)

        h = h*2
        VV.append(Va.dup())
        s = Sum(L)
        print("s")
        s.print()
        if bool(s > n):
            break


    I = InvPerm(J)

    LCP = Share([0]*n, 1<<d)

    d = len(VV)-2
    while d >= 0:
        V = VV[d].AppPerm(J)
    #    I1 = I[0:n]
    #    I2 = I[1:n+1]
    #    i = 0
    #    while i < n:
    #        I1[i] = I[i] + LCP[i]
    #        I2[i] = I[i+1] + LCP[i]
    #        i += 1
        I1 = I[0:n] + LCP
        I2 = I[1:n+1] + LCP
        V1 = V.BatchAccess(I1) # V1[i] := V[I1[i]] = V[I[i]  +LCP[i]]
        V2 = V.BatchAccess(I2) # V2[i] := V[I2[i]] = V[I[i+1]+LCP[i]]
    #    print("V1 ")
    #    V1.print()
    #    print("V2 ")
    #    V2.print()
        c = (V1 == V2)
    #    print("c ")
    #    c.print()
        c = c * (1<<d)
        LCP += c
        d -= 1

    return (I, LCP)

def merge(X, Y, rank_Y):
    if len(Y) != len(rank_Y):
        print('merge')
        Y.print()
        rank_Y.print()
        return None
    U = rank_Y.Unary(len(X)+1)[1:]
    pi = StableSort(U)
    Z = X @ Y
    ans = Z.AppPerm(pi)
    return ans

def getrank(sigma):
    n2 = sigma.len()//2
    q = sigma.order()
    B = Share([0]*n2 + [1]*n2, q)
    Ba = B.AppInvPerm(sigma)
    Bb = PrefixSum(Ba)
    Bc = Bb.AppPerm(sigma)
    r  = Bc[:n2]
    return r


def SuffixSort_DC3(T):
    n = len(T)
    print('SuffixSort_DC3 n = ', n, 'order = ', T.order())

    if n < 10:
        return SuffixSort(T)

# T12 を作る
    n2 = (n+3)//3
    o = T.order() + 3
    k = max(o, n+1) # !!!
    d = blog(k-1)+1

    T12 = [None] * 3
    d2 = max(d, blog(o+1)+1)
    Tp = T.extend(1<<d2)
    i = 0
    while i < n:
        Tp[i] = Tp[i] + 3
        i += 1
    Tp = Tp @ [2,1,0,0,0]


    j = 0
    while j < 3:
        T12[j] = Share([0] * (n2*2), 1<<d2)
#        T12[j] = Share().const(n2*2, 0, 1<<d2)
        j += 1
    i = 0
    while i < n2:
        j = 0
        while j < 3:
            T12[j][i] = Tp[i*3+1+2-j]
            j += 1
    #    T12pos[i] = i*3+1
        i += 1
    i = 0
    while i < n2:
        j = 0
        while j < 3:
            T12[j][n2+i] = Tp[i*3+2+2-j]
            j += 1
    #    T12pos[n2+i] = i*3+2
        i += 1
    T12a = [None] * 3
    j = 0
    while j < 3:
        T12a[j] = T12[j].A2B(1<<d2)
        j += 1
    T12b = T12a[0] ** T12a[1] ** T12a[2]
    J = T12b.sort() #  1文字でのソートを表す置換
#    print('J')
#    J.print()

    Wb = T12b.AppInvPerm(J) # 1文字のソート結果 (pos -> lex)
#    print('Wb')
#    Wb.print()
    L = Grouping_bits(Wb) # グループの境界を求める
#    print('L')
#    L.print()

    d3 = blog(len(L)+2-1)+1
    V = Grouping_name(L, 1<<d3)
#    V = rank1(L)
#    print('V')
#    V.print()

    T12c = V.AppPerm(J)
 #   print('T12c')
 #   T12c.print()
    T12c = T12c[:-1]

#    SA12 = SuffixSort(T12c)
    SA12 = SuffixSort_DC3(T12c)
#    print('SA12')
#    SA12.print()
#    s = L.extend(1<<d3).sum().get()[0]
#    print('sum', s)
#    if s < len(T12c)+1:
#        SA12 = SuffixSort_DC3(T12c)
#    else:
#        SA12 = InvPerm(J)


    SA12 = SA12.extend(1<<d)
    SA12inv = InvPerm(SA12)
#    print('SA12inv')
#    SA12inv.print()

    n02 = n2*2

    T01 = Share([0] * n02, Tp.order())
    SA01 = Share([0] * n02, SA12inv.order())
#    T01 = Share().const(n02, 0, Tp.order())
#    SA01 = Share().const(n02, 0, SA12inv.order())
    i = 0
    while i < n2:
        T01[i] = Tp[i*3+0]
        SA01[i] = i*3+0
        i += 1
    i = 0
    while i < n2:
        T01[n2+i] = Tp[i*3+1]
        SA01[n2+i] = i*3+1
        i += 1

    T01x = T01.AppInvPerm(SA12inv)
    T01xb = T01x.A2B(1<<d2)
    sigma3 = T01xb.sort()
    sigma = sigma3.AppPerm(SA12inv)


    B01 = Share([0]*n2 + [1]*n2, 1<<d)
    B01a = B01.AppInvPerm(sigma)  # 後で使う
    B01b = PrefixSum(B01a)
    B01c = B01b.AppPerm(sigma)
    r1 = B01c[:n2] # rank
#    r1 = getrank(sigma)

    T021 = Share([0] * (n02), Tp.order())
    T022 = Share([0] * (n02), Tp.order())
    R02 = Share([0] * (n02), SA12inv.order())
    i = 0
    while i < n2:
        T021[i] = Tp[i*3+0]
        T022[i] = Tp[i*3+1]
        R02[i] = SA12inv[n2+i]
        i += 1
    i = 0
    while i < n2:
        T021[n2+i] = Tp[i*3+2]
        T022[n2+i] = Tp[i*3+3]
        if i+1 < n2:
            R02[n2+i] = SA12inv[i+1]
        i += 1
    R02[n2*2-1] = SA12inv[0]
    T021b = T021.A2B(1<<d2)
    T022b = T022.A2B(1<<d2)

    K02c = T022b ** T021b
    T02x = K02c.AppInvPerm(R02)
    sigma4 = T02x.sort()
    sigma2 = sigma4.AppPerm(R02)


    B02 = Share([0]*n2 + [1]*n2, 1<<d)
    B02a = B02.AppInvPerm(sigma2)
    B02b = PrefixSum(B02a)
    B02c = B02b.AppPerm(sigma2)
    r2 = B02c[:n2]
#    r2 = getrank(sigma2)


    T12pos = Share([0] * (n2*2), 1<<d)
#    T12pos = Share().const(n2*2, 0, 1<<d)
    i = 0
    while i < n2:
        T12pos[i] = i*3+1
        T12pos[n2+i] = i*3+2
        i += 1
    SA12t = T12pos.AppPerm(SA12)

    rho2 = StableSort(B01a)
    SA01a = SA01.AppInvPerm(sigma)
    SA01t = SA01a.AppInvPerm(rho2)[:n2]

    R = r1 + r2
#    U = R.Unary(n2*2+1)[1:]
#    pi = StableSort(U)
#    SAtmp = SA12tmp2 @ SA01t
#    SA = SAtmp.AppPerm(pi)
    SA = merge(SA12t, SA01t, R)

    if SA.len() > n+1:
        SA = SA[SA.len()-(n+1):]

    return SA

def Suffix_print(T, SA):
    n = len(T)
    i = 0
    while i <= n:
        j = SA[i]
        print('SA[',i,'] = ', j, ' ', end='')
        while j < n:
            print(chr(T[j]), end='')
            j += 1
        print()
        i += 1
