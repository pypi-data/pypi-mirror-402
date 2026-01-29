#ifndef _LOUDS_H
 #define _LOUDS_H

#include "share.h"

/***********************************************
def LOUDS_parent(b):
  n = len(b)
  p = rank1(b)
  sigma = StableSort(b)
  v = AppInvPerm(p, sigma)
  parent = vsub(v[:n//2],[1]*(n//2)) # 正解
  return parent
***********************************************/
static _ LOUDS_parent(_ b)
{
  int n = len(b);
  _ p = rank1(b);
  _ sigma = StableSort(b);
  _ v = AppInvPerm(p, sigma);
//  _ v2 = AppPerm(p, sigma);
//  printf("LOUDS_parent v:  "); _print(v);
//  printf("LOUDS_parent v2: "); _print(v2);
  _ parent = _slice(v, 0, n/2);
  for (int i=0; i<len(parent); i++) {
    _addpublic(parent, i, -1);
  }

  _free(p);
  _free(sigma);
  _free(v);

  return parent;
}

/************************************************
def LOUDS_firstchild(b):
  b = b[1:]
  n = len(b)
  q = rank0(b)
  sigma = StableSort(b)
  v = AppInvPerm(q, sigma)
  firstchild = vadd(v[n//2:],[1]*(n//2)) # 正解
  return firstchild
************************************************/
static _ LOUDS_firstchild(_ bb)
{
  _ b = _slice(bb, 1, len(bb));

  int n = len(b);
  _ Q = rank0(b);
  _ sigma = StableSort(b);
  _ v = AppInvPerm(Q, sigma);
  _ firstchild = _slice(v, n/2, n);
  for (int i=0; i<len(firstchild); i++) {
    _addpublic(firstchild, i, 1);
  }
  _free(b);
  _free(Q);
  _free(sigma);
  _free(v);

  return firstchild;

}

/************************************************
def LOUDS_contract(b):
  b = b[1:]
  n = len(b)
  p = rank1(b)
  q = rank0(b)
  sigma = StableSort(b)
  r = IfThenElse(b, q, p)
  v0 = AppInvPerm(r, sigma)
  v1 = v0[1+n//2:]+[n//2]+v0[0:n//2]
  v = AppPerm(v1, sigma)
  d10 = Propagate(vneg(b), v)
  d1 = vsub(d10, r)
  d00 = Propagate([1]+b, [0]+v)[1:]  # 各ノード v の親の ID を，v の子にコピーする
  d0 = vsub(d00, r)
  d = IfThenElse(b, d1, d0)
  pi = vadd(d, Perm_ID(n))
  bb = [1] + AppInvPerm(b, pi)
  return (bb, pi) # pi は元のLOUDSから新しいLOUDSへの変換を表す置換
************************************************/
static _pair LOUDS_contract(_ b_)
{
  _ b = _slice(b_, 1, len(b_));
  int n = len(b);
  //printf("LOUDS_contract b :"); _print(b);
  _ p = rank1(b);
  _ q = rank0(b);
  _ sigma = StableSort(b);
  _ r = IfThenElse(b, q, p);
//  printf("sigma "); _print(sigma);
//  printf("r "); _print(r);
  _ v0 = AppInvPerm(r, sigma);
//  printf("v0 "); _print(v0);
  _ v1 = _dup(v0);
  _setshares(v1, 0, (n/2)-1, v0, (n/2)+1);
  _setpublic(v1, (n/2)-1, n/2);
  _setshares(v1, n/2, (n/2)*2, v0, 0);
//  printf("v1 "); _print(v1);
  _ v  = AppPerm(v1, sigma);
//  printf("v "); _print(v);
  _ bneg = vneg(b);
  _ d1 = Propagate(bneg, v);
//  printf("d10 "); _print(d1);
  vsub_(d1, r);
//  printf("d1 "); _print(d1);
  _ b1 = _insert_head(b, 1);
  _ zv = _insert_head(v, 0);
  _ d0 = Propagate(b1, zv);
//  printf("d00 "); _print(d0);
  _slice_(d0, 1, len(d0));
  vsub_(d0, r);
//  printf("d0 "); _print(d0);
  _ d = IfThenElse(b, d1, d0);
//  printf("d "); _print(d);
  _ perm = Perm_ID2(len(b), order(d));
  _ pi = vadd(d, perm);
//  printf("pi "); _print(pi);
  _ bb = AppInvPerm(b, pi);
  _insert_head_(bb, 1);
//  printf("bb "); _print(bb);
  _pair tmp = {bb, pi};

  _free(b);
  _free(p);
  _free(q);
  _free(sigma);
  _free(r);
  _free(v0);
  _free(v1);
  _free(v);
  _free(bneg);
  _free(d1);
  _free(b1);
  _free(zv);
  _free(d0);
  _free(d);
  _free(perm);

  return tmp;
}

/******************************************************
def LOUDS_contract_easy(b):
  n = len(b)
  parent = LOUDS_parent(b)
  firstchild = vsub(LOUDS_firstchild(b), [1]*(n//2))
  b = b[1:]
  sigma = StableSort(b)
  r = AppPerm(parent+firstchild, sigma)
  d00 = [0] + BatchAccessUnary(parent, vneg(b)[1:])
  d10 = BatchAccessUnary(firstchild+[n//2], [0]+b)
  d = vsub(AppPerm(d00+d10, sigma), r)
  pi = vadd(d, Perm_ID(n))
  bb = [1] + AppInvPerm(b, pi)
  return (bb, pi) # pi は元のLOUDSから新しいLOUDSへの変換を表す置換
******************************************************/
static _pair LOUDS_contract_easy(_ b_)
{
  int n = len(b_);

  _ parent = LOUDS_parent(b_);
  _ firstchild = LOUDS_firstchild(b_);
  for (int i=0; i<len(firstchild); i++) {
    _addpublic(firstchild, i, -1);
  }

  _ b = _slice(b_, 1, len(b_));
  _ sigma = StableSort(b);
  _ pf = _concat(parent, firstchild);
  _ r = AppPerm(pf, sigma);
  _ bneg = vneg(b);
  _slice_(bneg, 1, len(bneg));
  _ d00 = BatchAccessUnary(parent, bneg);
  _insert_head_(d00, 0);
  _insert_tail_(firstchild, n/2);
  _ zb = _insert_head(b, 0);
  _ d10 = BatchAccessUnary(firstchild, zb);
  _ d2 = _concat(d00, d10);
  _ d = AppPerm(d2, sigma);
  vsub_(d, r);
  _ perm = Perm_ID(b);
  _ pi = vadd(d, perm);
  _ bb = AppInvPerm(b, pi);
  _insert_head_(bb, 1);

  _pair ans = {bb, pi};

  _free(b);
  _free(sigma);
  _free(pf);
  _free(r);
  _free(bneg);
  _free(d00);
  _free(zb);
  _free(d10);
  _free(d2);
  _free(d);
  _free(perm);
  _free(parent);
  _free(firstchild);

  return ans;
}

/**********************************************
def LOUDS_grandparent(b):
  parent = LOUDS_parent(b)
  p2 = [0] + BatchAccessUnary(parent, vneg(b[1:]))
  return p2
**********************************************/
static _ LOUDS_grandparent(_ b)
{
  _ parent = LOUDS_parent(b);
  _ bb = _slice(b, 1, len(b));
  _ bneg = vneg(bb);
  _slice_(bneg, 1, len(bneg));
  _ p2 = BatchAccessUnary(parent, bneg);
  _insert_head_(p2, 0);

  _free(parent);
  _free(bneg);
  _free(bb);
  return p2;
}

/**********************************************
def LOUDS_grandchild(b):
  n = len(b)//2
  firstchild = LOUDS_firstchild(b)
  c2 = BatchAccessUnary(firstchild+[n+1], [0]+b)[1:]
  return c2
**********************************************/
static _ LOUDS_grandchild(_ b)
{
  int n = len(b)/2;
  _ firstchild = LOUDS_firstchild(b);
  _insert_tail_(firstchild, n+1);
  _ zb = _insert_head(b, 0);
  _ c2 = BatchAccessUnary(firstchild, zb);
  _slice_(c2, 1, len(c2));

  _free(firstchild);
  _free(zb);
  return c2;
}

/**********************************************
def select0_from_parent(parent):
  n = len(parent)
  pi = vadd(parent, vadd(Perm_ID(n), [1]*n))
  return pi

def select1_from_child(firstchild):
  n = len(firstchild)
  pi = [0] + vadd(firstchild, Perm_ID(n))
  return pi
**********************************************/
static _ select0_from_parent(_ parent)
{
  int n = len(parent);
  _ pi = _dup(parent);
  for (int i=0; i<n; i++) _addpublic(pi, i, i+1);
  return pi;
}

static _ select1_from_child(_ firstchild)
{
  int n = len(firstchild);
  _ pi = _dup(firstchild);
  for (int i=0; i<n; i++) _addpublic(pi, i, i);
  _insert_head_(pi, 0);
  return pi;
}

/**********************************************
def ArrayToLOUDS(parent, firstchild):
  n = len(parent)
  pi1 = select0_from_parent(parent)
  pi2 = select1_from_child(firstchild)
  pi = pi1 + pi2
  b = [0] * n + [1] * (n+1)
  L = AppInvPerm(b, pi)
  return (L, pi)
**********************************************/
static _pair ArrayToLOUDS(_ parent, _ firstchild)
{
  int n = len(parent);
  _ pi1 = select0_from_parent(parent);
  _ pi2 = select1_from_child(firstchild);
  _ pi = _concat(pi1, pi2);
//  _ b0 = share_const(n, 0, 2); // 2値でなく order(parent) の方が良い?
//  _ b1 = share_const(n+1, 1, 2); //
  _ b0 = _const(n, 0, order(parent));
  _ b1 = _const(n+1, 1, order(parent));
  _ b = _concat(b0, b1);
  _ L = AppInvPerm(b, pi);
  _pair ans = {L, pi};

  _free(pi1);
  _free(pi2);
  _free(b0);
  _free(b1);
  _free(b);
  return ans;
}

/**********************************************
def LOUDS_contract_easy2(b):
  n = len(b)//2

  parent = LOUDS_parent(b)
  firstchild = LOUDS_firstchild(b)

  pp = [0] + BatchAccessUnary(parent, vneg(b[1:])) # grandparent
  cc = BatchAccessUnary(firstchild+[n+1], [0]+b) #grandchild

  (L, pi) = ArrayToLOUDS(pp, cc)

  return L
**********************************************/
static _ LOUDS_contract_easy2(_ b_)
{
  int n = len(b_)/2;

  _ parent = LOUDS_parent(b_);
  _ firstchild = LOUDS_firstchild(b_);

  _ b = _slice(b_, 1, len(b_));
  _ bneg = vneg(b);
  _slice_(bneg, 1, len(bneg));
  _ pp = BatchAccessUnary(parent, bneg);
  _insert_head_(pp, 0);

  _insert_tail_(firstchild, n+1);
  _ zb = _insert_head(b, 0);
  _ cc = BatchAccessUnary(firstchild, zb);

  _pair tmp = ArrayToLOUDS(pp, cc);
  _ L = tmp.x;
  _ pi = tmp.y;

  _free(parent);
  _free(bneg);
  _free(pp);
  _free(firstchild);
  _free(zb);
  _free(pi);
  _free(cc);
  _free(b);

  return L;
}

/**********************************************
def LOUDS_contract_supereasy(b):
  p2 = LOUDS_grandparent(b)
  c2 = LOUDS_grandchild(b)
  (L, pi) = ArrayToLOUDS(p2, c2)
  return L
}
**********************************************/
static _ LOUDS_contract_supereasy(_ b)
{
  _ p2 = LOUDS_grandparent(b);
  _ c2 = LOUDS_grandchild(b);
  _pair tmp = ArrayToLOUDS(p2, c2);
  _ L = tmp.x;
  _ pi = tmp.y;

  _free(p2);
  _free(c2);
  _free(pi);
  return L;
}

/***************************************************
def PathSum(b, w):
  bb = b

  sigma = StableSort(bb[1:])
  wb = [0]+AppPerm(w+w, sigma)


  n = len(b)//2
  b0 = bb
  s0 = wb
  r = 1
  while r <= n:
    sigma0 = StableSort(b0)
    d0 = Propagate(b0, s0)
    e1 = AppInvPerm(vadd(s0,d0), sigma0)
    (b1, rho0) = LOUDS_contract(b0)
    z1 = e1[:n] + [0] + e1[:n]
    c1 = AppPerm(z1, sigma0)
    s1 = AppInvPerm(c1[1:], rho0)
    r *= 2
    b0 = b1
    s0 = [0]+s1
  return z1[0:n]
***************************************************/
static _ PathSum(_ b, _ w)
{
  int n = len(b)/2;
  _ b0 = _dup(b);
  _ bb1 = _slice(b0, 1, len(b0));

  _ sigma = StableSort2(bb1);
  _free(bb1);
  _ w2 = _concat(w, w);
  //printf("w2 "); _print(w2);
  //printf("sigma "); _print(sigma);
  _ s0 = AppPerm(w2, sigma);
  _free(w2);
  _free(sigma);
  _insert_head_(s0, 0);

//  _ b0 = share_dup(bb);
//  _ s0 = share_dup(wb);
  int r = 1;
  _ z1 = _const(1, 0, 1); // dummy
  while (r <= n) {
    _ b0tmp = _shrink(b0, 2);
    _ sigma0 = StableSort2(b0tmp);
    _free(b0tmp);
    //_ d0 = Propagate2(b0, s0);
    _ d0 = Propagate(b0, s0);
    vadd_(s0, d0);
    _ e1 = AppInvPerm(s0, sigma0);
    _pair tmp = LOUDS_contract(b0);
    _ b1 = tmp.x;
    _ rho0 = tmp.y;
    _ ztmp = _slice(e1, 0, n);
    _free(z1);
    z1 = _insert_tail(ztmp, 0);
    _concat_(z1, ztmp);
    //printf("z1 "); _print(z1);
    //printf("sigma0 "); _print(sigma0);
    _ c1 = AppPerm(z1, sigma0);
    _slice_(c1, 1, len(c1));
    _ s1 = AppInvPerm(c1, rho0);
    r = r*2;
//    _free(b0);
//    b0 = _dup(b1);
//    _free(b1);
    _move_(b0, b1);
    _free(e1);
    _free(s0);
    _free(rho0);
    _free(ztmp);
    s0 = _insert_head(s1, 0);
    _free(s1);
    _free(sigma0);
    _free(d0);
    _free(c1);
  }
  _ ans = _slice(z1, 0, n);
  _free(z1);
  _free(b0);
  _free(s0);

  return ans;
}

/***************************************************
def PathSum_easy(b, w):
  pi = [0] + LOUDS_parent(b)
  w = [0] + w
  n = len(w)
  d = 1
  while d < n:
    print('pi', pi)
    I = Unary(pi, n)
    print('I', I)
    wp = BatchAccessUnary(w, I)
    print('wp', wp)
    w2 = vadd(w, wp)
    print('w2', w2)
    w = w2
    pi2 = BatchAccessUnary(pi, I)
    print('pi2', pi2)
    pi = pi2
    d *= 2
  return w[1:]
***************************************************/
#if 0
static _ PathSum_easy(_ b, _ w_)
{
  _ pi = LOUDS_parent(b);
  _insert_head_(pi, 0);
  _ w = _insert_head(w_, 0);
  int n = len(w);
  int d = 1;
  while (d < n) {

  }
}
#endif
/***************************************************
def LOUDS_get_parent(w, b):
  I = vneg([1,0]+b[1:])
  wp = BatchAccessUnary(w, I)
  return wp

def PathSum_supereasy(b, w):
  w = [0] + w
  n = len(w)
  d = 1
  while d < n:
    wp = LOUDS_get_parent(w, b)
    w = vadd(w, wp)
    b = LOUDS_contract_easy(b)[0]
    d *= 2
  return w[1:]
***************************************************/
static _ LOUDS_get_parent(_ w, _ b_)
{
  _ b = _slice(b_, 1, len(b_));
  _insert_head_(b, 0);
  _insert_head_(b, 1);
  _ I = vneg(b);
  _ wp = BatchAccessUnary(w, I);
  _free(b);
  _free(I);

  return wp;
}

static _ PathSum_supereasy(_ b_, _ w_)
{
  _ b = _dup(b_);
  _ w = _insert_head(w_, 0);
  int n = len(w);
  int d = 1;
  while (d < n) {
    _ wp = LOUDS_get_parent(w, b);
    vadd_(w, wp);
    _free(wp);
    _pair tmp = LOUDS_contract_easy(b);
    _free(b);
    b = tmp.x;
    _free(tmp.y);
    d = d*2;
  }
  _slice_(w, 1, len(w));
  _free(b);
  return w;
}

/***************************************************
def TreeSum(b, w):
  bb = b[1:]

  sigma = StableSort(bb)
  wb = AppPerm(w+w, sigma)

  n = len(b)//2
  b0 = bb
  s0 = wb
  r = 1
  while r <= n:
    sigma0 = StableSort(b0)
    p0 = SuffixSum(s0)
    e1 = AppInvPerm(p0, sigma0)
    z2 = vsub(e1[n:],e1[n+1:]+[0])
    z1 = z2 + z2
    (b1, rho0) = LOUDS_contract([1]+b0)
    c1 = AppPerm(z1, sigma0)
    s1 = AppInvPerm(c1, rho0)
    r *= 2
    b0 = b1[1:]
    s0 = s1
  return z1[0:n]
***************************************************/
static _ TreeSum(_ b, _ w)
{
  _ bb = _slice(b, 1, len(b));
  _ sigma = StableSort(bb);
  _ w2 = _concat(w, w);
  _ wb = AppPerm(w2, sigma);
  _free(w2);
  _free(sigma);

  int n = len(b)/2;
//  _ b0 = _dup(bb);
//  _free(bb);
//  _ s0 = _dup(wb);
//  _free(wb);
  _ b0 = bb;
  _ s0 = wb;
//  printf("TreeSum\n");
//  printf("b0 "); _print(b0);
//  printf("s0 "); _print(s0);
  _ z1 = _const(1, 0, 1);
  int r = 1;
  while (r <= n) {
    _ sigma0 = StableSort(b0);
//    printf("sigma0 "); _print(sigma0);
    _ p0 = SuffixSum(s0);
//    printf("p0 "); _print(p0);
    _ e1 = AppInvPerm(p0, sigma0);
    _free(p0);
//    printf("e1 "); _print(e1);
    _ z20 = _slice(e1, n, len(e1));
    _ z21 = _slice(e1, n+1, len(e1));
    _free(e1);
    _insert_tail_(z21, 0);
    _ z2 = vsub(z20, z21);
    _free(z20);
    _free(z21);
    _free(z1);
    z1 = _concat(z2, z2);
    _free(z2);
//    printf("z1 "); _print(z1);
    _ b01 = _insert_head(b0, 1);
    _pair tmp = LOUDS_contract(b01);
    _free(b01);
    _ b1 = tmp.x;
    _ rho0 = tmp.y;
//    printf("rho0 "); _print(rho0);
//    printf("b1 "); _print(b1);
    _ c1 = AppPerm(z1, sigma0);
    _ s1 = AppInvPerm(c1, rho0);
//    printf("c1 "); _print(c1);
//    printf("s1 "); _print(s1);
    r = r*2;
    _free(c1);
    _free(b0);
    _free(sigma0);
    b0 = _slice(b1, 1, len(b1));
//    _free(s0);
//    s0 = _dup(s1);
//    _free(s1);
    _move_(s0, s1);
    _free(b1);
    _free(rho0);
//    printf("b0 "); _print(b0);
//    printf("s0 "); _print(s0);

  }
  _ ans = _slice(z1, 0, n);
  _free(b0);
  _free(s0);
  _free(z1);

  return ans;
}

/*****************************************************
# 各ノードの値を LOUDS 上の対応する 0,1 の位置にコピー
# LOUDS は先頭の 1 を含まない形式
def LOUDS_Distribute(wp, wc, b):
  sigma = StableSort(b)
  wb = AppPerm(wc+wp, sigma)
  return wb

def LOUDS_Duplicate(w, b):
  return LOUDS_Distribute(w, w, b)
*****************************************************/
_ LOUDS_Distribute(_ wp, _ wc, _ b)
{
  _ sigma = StableSort(b);
  _ ww = _concat(wc, wp);
  _ wb = AppPerm(ww, sigma);
  _free(sigma);
  _free(ww);
  return wb;
}

_ LOUDS_Duplicate(_ w, _ b)
{
  return LOUDS_Distribute(w, w, b);
}


/*****************************************************
# 各ノードの値を集めた配列を作る
# LOUDS は先頭の 1 を含まない形式
def LOUDS_gather(wb, b):
  n = len(b)//2
  sigma0 = StableSort(b)
  print('sigma0', sigma0)
  e1 = AppInvPerm(wb, sigma0)
  print('e1', e1)
  return e1[n:]

*****************************************************/
_ LOUDS_gather(_ wb, _ b)
{
  int n = len(b)/2;
  _ sigma0 = StableSort(b);
  _ e1 = AppInvPerm(wb, sigma0);
  _slice_(e1, n, len(e1));
  _free(sigma0);
  return e1;
}


/*****************************************************
def TreeSum_easy(b, w):
  bb = b[1:]

  wb = LOUDS_Duplicate(w, bb)

  n = len(b)//2
  b0 = bb
  s0 = wb
  r = 1
  while r <= n:
    p0 = SuffixSum(s0)
    e1 = LOUDS_gather(p0, b0)
    z2 = vsub(e1, lshift(e1,0))
    (b1, rho0) = LOUDS_contract([1]+b0)
    s1 = LOUDS_Duplicate(z2, b1[1:])
    r *= 2
    b0 = b1[1:]
    s0 = s1
  return z2
*****************************************************/
_ TreeSum_easy(_ b, _ w)
{
  _ bb = _slice(b, 1, len(b));

  _ wb = LOUDS_Duplicate(w, bb);

  int n = len(b)/2;
//  _ b0 = _dup(bb);
//  _free(bb);
    _ b0 = bb;
//  _ s0 = _dup(wb);
//  _free(wb);
  _ s0 = wb;
  int r = 1;
  _ z2 = _const(1, 0, order(w));
  while (r <= n) {
    _ p0 = SuffixSum(s0);
    _ e1 = LOUDS_gather(p0, b0);
    _free(p0);
    _ e10 = lshift(e1,0);
    _free(z2);
    z2 = vsub(e1, e10);
    _free(e1);
    _free(e10);
    _ b01 = _insert_head(b0, 1);
    _pair tmp = LOUDS_contract(b01);
    _free(b01);
    _ b1 = tmp.x;
    _free(b0);
    b0 = _slice(b1, 1, len(b1));
    _free(b1);
    _free(tmp.y);
    _free(s0);
    s0 = LOUDS_Duplicate(z2, b0);
    r = r*2;
  }
  _free(b0);
  _free(s0);
  return z2;
}

/*****************************************************
# 各ノードに対し，そのノードの全ての子の値の和を求める
# LOUDS は先頭の 1 を含まない形式
def LOUDS_sum_children(wc, b):
  n = len(b)//2
  sigma = StableSort(b)
#  wb = AppPerm(wc+wp, sigma)
  wb = AppPerm(wc+[0]*n, sigma)
#  print('wb', wb)
  s = SuffixSum(wb)
#  print('s', s)
  e = LOUDS_gather(s, b)
#  print('e', e)
  z = vsub(e, lshift(e,0))
  return z

def TreeSum_supereasy(b, w):
  n = len(b)//2
  r = 1
  while r <= n:
    wc = LOUDS_sum_children(w, b[1:])
    w = vadd(w, wc)
    b = LOUDS_contract(b)[0]
    r *= 2
  return w
*****************************************************/
_ LOUDS_sum_children(_ wc, _ b)
{
  int n = len(b)/2;
  _ sigma = StableSort(b);
  _ zeros = _const(n, 0, order(wc));
  _ wc0 = _concat(wc, zeros);
  _ wb = AppPerm(wc0, sigma);
  _free(sigma);
  _free(zeros);
  _free(wc0);
  _ s = SuffixSum(wb);
  _free(wb);
  _ e = LOUDS_gather(s, b);
  _free(s);
  _ e0 = lshift(e, 0);
  _ z = vsub(e, e0);
  _free(e);
  _free(e0);

  return z;
}

_ TreeSum_supereasy(_ b_, _ w_)
{
  int n = len(b_)/2;
  int r = 1;
  _ b = _dup(b_);
  _ w = _dup(w_);
  while (r <= n) {
    _ b1 = _slice(b, 1, len(b));
    _ wc = LOUDS_sum_children(w, b1);
    _free(b1);
    vadd_(w, wc);
    _free(wc);
    _pair tmp = LOUDS_contract(b);
    _free(b);
    b = tmp.x;
    _free(tmp.y);
    r = r*2;
  }
  _free(b);
  return w;
}

/***************************************************
def LOUDS_depth(b):
  n = len(b)//2
  w = [1]*n
#  print('b', b)
#  print('w', w)
  return PathSum(b, w)

def LOUDS_treesize(b):
  n = len(b)//2
  w = [1]*n
#  print('b', b)
#  print('w', w)
  return TreeSum(b, w)

def LOUDS_ancestors(b):
  n = len(b)//2
  w = vadd(Perm_ID(n), [1]*n)
#  print('b', b)
#  print('w', w)
  return PathSum(b, w)

def LOUDS_degree(b):
  n = len(b)//2
#  wp = [0] * n
  wc = [1] * n
  z = LOUDS_sum_children(wc, b)
  return z
***************************************************/
_ LOUDS_depth(_ b)
{
  int n = len(b)/2;
  _ w = _const(n, 1, order(b));
  _ ans = PathSum(b, w);
  _free(w);
  return ans;
}

_ LOUDS_treesize(_ b)
{
  int n = len(b)/2;
  _ w = _const(n, 1, order(b));
  _ ans = TreeSum(b, w);
  _free(w);
  return ans;
}

_ LOUDS_ancestors(_ b)
{
  int n = len(b)/2;
  _ w = _const(n, 0, order(b));
  for (int i=0; i<n; i++) {
    _setpublic(w, i, i+1);
  }
  _ ans = PathSum(b, w);
  _free(w);
  return ans;
}

_ LOUDS_degree(_ b)
{
  int n = len(b)/2;
  _ wc = _const(n, 1, order(b));
  _ ans = LOUDS_sum_children(wc, b);
  _free(wc);
  return ans;
}

/***********************************************
def LOUDS_prerank(bb):
  n = len(bb)//2
  b = B2A(bb[1:])
  sigma = StableSort(b)
  d = LOUDS_depth(bb)
  e = [1]+vsub(d[1:],d[:-1])
  f = B2Ainv(e)
  s = LOUDS_treesize(bb)
  f1 = AppPerm([0]*n + f, sigma) # 各レベルの最初の位置
  s0 = AppPerm(s + [0]*n, sigma)
  bs = PrefixSum(vneg(b)) # 子の ID
  h1 = IfThenElse(f1, bs, [0]*(2*n)) # 各レベルの最後のノードの ID

  p = PrefixSum(s0)
  pp = Propagate([1]+f1, [0]+vsub(p, h1))[1:]
  q = vsub(p, pp)
  q = vsub(q, s0)
  q = vsub(q, PrefixSum(h1))

  x = AppInvPerm(q, sigma)[:n]
  a = LOUDS_ancestors(bb)
  z = vadd(x, a)
  z = vsub(z, Perm_ID(n))
  return z
***********************************************/
_ LOUDS_prerank(_ bb)
{
  //printf("prerank: bb "); _print(bb);
  int n = len(bb)/2;
  _ b = _slice(bb, 1, len(bb));
  _ sigma = StableSort(b);
  _ d = LOUDS_depth(bb);
  //printf("prerank: d "); _print(d);
  _ e = _slice(d, 1, len(d));
  _ e2 = _slice(d, 0, len(d)-1);
  _free(d);
  vsub_(e, e2);
  _free(e2);
  _insert_head_(e, 1);
//  _ f = _dup(e);
  _ s = LOUDS_treesize(bb);
  _ f0 = _const(n, 0, order(e));
//  _concat_(f0, f);
  _concat_(f0, e);
  _free(e);
  _ f1 = AppPerm(f0, sigma); // 各レベルの最初の位置
  _free(f0);
//  _free(f);
  _ s1 = _const(n, 0, order(s));
  _ s2 = _concat(s, s1);
  _ s0 = AppPerm(s2, sigma);
  _free(s);
  _free(s1);
  _free(s2);
  _ bneg = vneg(b);
  _ bs = PrefixSum(bneg); // 子の ID
  _free(bneg);
  _ zeros = _const(2*n, 0, order(bs));
  //_ h1 = IfThenElse(f1, bs, zeros); // 各レベルの最後のノードの ID
  //printf("f1 "); _print(f1);
  //printf("bs "); _print(bs);
  _move_(f1, _shrink(f1, 2));
  _ h1 = IfThen_b(f1, bs); // 各レベルの最後のノードの ID
  _free(zeros);
  _free(bs);
  _free(b);

  _ p = PrefixSum(s0);
  _insert_head_(f1, 1);
  _ p0 = vsub(p, h1);
  _insert_head_(p0, 0);
  //_ pp = Propagate2(f1, p0);
  _ pp = Propagate(f1, p0);
  _free(p0);
  _free(f1);
  _slice_(pp, 1, len(pp));
  _ q = vsub(p, pp);
  _free(p);
  _free(pp);
  vsub_(q, s0);
  _ ph1 = PrefixSum(h1);
  vsub_(q, ph1);
  _free(ph1);
  _free(h1);
  _free(s0);

  _ x = AppInvPerm(q, sigma);
  _slice_(x, 0, n);
  _ a = LOUDS_ancestors(bb);
  _ z = vadd(x, a);
  _ pid = Perm_ID2(len(z), order(z));
  vsub_(z, pid);
  _free(x);
  _free(a);
  _free(q);
  _free(pid);
  _free(sigma);
  return z;

}


/**********************************************
def LOUDS_to_BP(bb):
  n = len(bb)//2
  b =bb[1:]
  sigma = StableSort(b)
  d = LOUDS_depth(bb)
  s = LOUDS_treesize(bb)
  z = LOUDS_prerank(bb)
  v = smul(2, z)
  v = vsub(v, [1]*n)
  v = vsub(v, d) # 開き括弧の位置
  w = smul(2, s)
  w = vsub(w, [1]*n)
  w = vadd(w, v) # 閉じ括弧の位置
  pi = AppPerm(v+w, sigma)
  bp = AppInvPerm(b, pi)
  BP = ''
  for c in bp:
    if c == 0:
      BP += '('
    else:
      BP += ')'
  return (BP, pi)
**********************************************/
_pair LOUDS_to_BP(_ bb)
{
  int n = len(bb)/2;
  _ b = _slice(bb, 1, len(bb));
  _ sigma = StableSort2(b);
  //printf("sigma "); _print(sigma);
  _ d = LOUDS_depth(bb);
  _ s = LOUDS_treesize(bb);
  _ z = LOUDS_prerank(bb);
  _ v = smul(2, z);
  _free(z);
  _ c = _const(n, 1, order(v));
  vsub_(v, c);
  vsub_(v, d); //  開き括弧の位置
  _ w = smul(2, s);
  _free(s);
  _free(d);
  vsub_(w, c);
  _free(c);
  vadd_(w, v); //  閉じ括弧の位置
  _ vw = _concat(v, w);
  _ pi = AppPerm(vw, sigma);
  _ bp = AppInvPerm(b, pi);
  _pair ans = {bp, pi};
  _free(v);
  _free(w);
  _free(vw);
  _free(sigma);
  _free(b);
  return ans;
}

/***********************************************
def BP_to_Excess(BP):
  N = len(BP)
  D = [0] * (N+1)
  D[0] = (0, 0, 1) # (depth, pos, b)
  i = 0
  d = 0
  while i < N:
    if BP[i] == '(':
      d += 1
      D[i+1] = (d, i+1, 1)
    else:
      d -= 1
      D[i+1] = (d, i+1, 0)
    i += 1
  return D

def BP_to_LOUDS(BP):
  N = len(BP)
  D = BP_to_Excess(BP)

  D.sort() # log N rounds
  LOUDS = [b for (d, i, b) in D] # + [1]
  sigma = [i for (d, i, b) in D]
  return (LOUDS, sigma)
***********************************************/
////////////////////////////////////////
// 開き括弧は 0, 閉じ括弧は 1 とする
////////////////////////////////////////
# define OP 0
# define CP 1
_pair BP_to_LOUDS(_ BP)
{
  int n = len(BP);
  share_t q = order(BP);
//  share_t q = 1 << blog(n+1);
  _ P = _dup(BP);

  //printf("P "); _print(P);
  _smul_(q-2, P);
  //printf("P "); _print(P);
  for (int i=0; i<n; i++) _addpublic(P, i, 1);
  //printf("P "); _print(P);
  _ D = PrefixSum(P);
  _insert_head_(D, 0);
  _ BP0 = _insert_head(BP, OP);
  //printf("BP0 "); _print(BP0);
  //printf("D   "); _print(D);

  _pair tmp = _radix_sort(D);
  _free(tmp.x);
  _ LOUDS = AppPerm(BP0, tmp.y);
  vneg_(LOUDS);
  _ sigma = tmp.y;
  //printf("sigma  "); _print(sigma);

  _pair ans = {LOUDS, sigma};

  _free(P);
  _free(D);
  _free(BP0);

  return ans;

}

#endif
