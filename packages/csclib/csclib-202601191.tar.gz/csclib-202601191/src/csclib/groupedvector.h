#include "share.h"

#if 0
def Diff(x:Share) -> Share:
  return x - rshift(x, 0) # x[i] - x[i-1], x[0] does not change

def GroupCountSort(g:Share, b:Share) -> Share:
  n = len(b)
  q = 2 ** (blog(n-1)+1)
  sigma = StableSort(g)
  if (b.order() == 2):
    b = b.B2A(q)
  if (g.order() == 2):
    g = g.B2A(q)
  r1 = PrefixSum(b).shrink(q)
  r0 = PrefixSum(~b).shrink(q)
  s1 = IfThen(g, rshift(r1, 0))
  s0 = IfThen(g, rshift(r0, 0))
  u1 = s1.AppInvPerm(sigma)
  u0 = s0.AppInvPerm(sigma)
  w1 = Diff(u1)
  w0 = lshift(u0, r0[n-1]) - u0
  y1 = w1.AppPerm(sigma)
  y0 = w0.AppPerm(sigma)
  y0[0] = y0[0] - 1
  y1[0] = y1[0] - 1
  z0 = r0 + PrefixSum(y1)
  z1 = r1 + PrefixSum(y0)
  pi = IfThenElse(b, z1, z0)
  return pi

#endif

#if 0
_ Diff(_ x)
{
  _ xtmp = rshift(x, 0);
  _ ans = vsub(x, xtmp);
  _free(xtmp);
  return ans;
}
#endif

_ GroupCountSort(_ g_, _ b_)
{
  int n = len(b_);
  share_t q = 1 << (blog(n-1)+1);
  _ sigma = StableSort2(g_);
  _ b;
  if (order(b_) == 2) {
    b = B2A(b_, q);
  } else {
    b = _dup(b_);
  }
  _ g;
  if (order(g_) == 2) {
    g = B2A(g_, q);
  } else {
    g = _dup(g_);
  }
  _ r1 = PrefixSum(b);
  _ bneg = vneg(b);
  _ r0 = PrefixSum(bneg);
  _ r1r = rshift(r1, 0);
  _ s1 = IfThen(g, r1r);
  _ r0r = rshift(r0, 0);
  _ s0 = IfThen(g, r0r);
  _ u1 = AppInvPerm(s1, sigma);
  _ u0 = AppInvPerm(s0, sigma);
  _ w1 = Diff(u1, 0);
  _ w0 = lshift(u0, share_getraw(r0, n-1));
  vsub_(w0, u0);
  _ y1 = AppPerm(w1, sigma);
  _ y0 = AppPerm(w0, sigma);
  _addpublic(y0, 0, q-1);
  _addpublic(y1, 0, q-1);
  _ y1p = PrefixSum(y1);
  _ z0 = vadd(r0, y1p);
  _ y0p = PrefixSum(y0);
  _ z1 = vadd(r1, y0p);
  _ pi = IfThenElse(b, z1, z0);
  _free(y1p); _free(y0p);
  _free(z0); _free(z1); _free(w0); _free(w1); _free(r0); _free(r1);
  _free(r0r); _free(r1r); _free(bneg); _free(y0); _free(y1); _free(u0); _free(u1);
  _free(s0); _free(s1);
  _free(g); _free(b); _free(sigma);
  return pi;
}

#if 0
def GroupStableSort(g:Share, B:Bits) -> Share:
  n = len(g)
  q = 2 ** (blog(n-1)+1)
  W = B.depth()
  pi = Share().const(n, 0, q)
  pi.setperm()
  print('pi')
  pi.print()
  b = B.get()
  d = W-1
  g_d = g
  while d >= 0:
    print('d =',d)
    x_d = b[d].AppInvPerm(pi)
    print('x_d')
    x_d.print()
    sigma_d = GroupCountSort(g_d, x_d)
    c_d = x_d.AppInvPerm(sigma_d)
    c_tmp = XOR(c_d, rshift(c_d, 0))
    g_d = OR(g_d, c_tmp)
    pi = sigma_d.AppPerm(pi)
    d -= 1
  return pi
#endif

_ GroupStableSort(_ g, _bits B)
{
  int n = len(g);
  share_t q = 1 << (blog(n-1)+1);
  int W = depth_bits(B);
  _ pi = Perm_ID2(n, q);
  _ g_d = _dup(g);
  for (int d = W-1; d >= 0; d--) {
    printf("d = %d\n", d);
    _ x_d = AppInvPerm(B->a[d], pi);
    printf("x_d "); _print_debug(x_d);
    _ sigma_d = GroupCountSort(g_d, x_d);
    _ c_d = AppInvPerm(x_d, sigma_d);
    //printf("c_d "); _print(c_d);
    _ c_d0 = rshift(c_d, 0);
    //printf("c_d0 "); _print(c_d0);
    _ c_tmp = XOR(c_d, c_d0);
    //printf("g_d "); _print(g_d);
    //printf("c_tmp "); _print(c_tmp);
    _ g_dtmp = OR(g_d, c_tmp);
    _move_(g_d, g_dtmp);
    _ pitmp = AppPerm(sigma_d, pi);
    _move_(pi, pitmp);
    _free(c_tmp); _free(c_d0); _free(c_d); _free(sigma_d); _free(x_d);
  }
  _free(g_d);
  return pi;
}

#if 0
def adjustlen(x:Share, n:int) -> Share:
  if len(x) < n:
    x = ([0] * (n-len(x))) @ x
  elif len(x) > n:
    x = x[-n:]
  return x

def DynAccess(g:Share, f:Share, v:Share) -> Share:
  N = len(g)
  tau = StableSort(f)
  sigma = StableSort(g)
  vp = IfThen(f, v)
  w = vp.AppInvPerm(tau)
  w = adjustlen(w, N)
  x = Diff(w)
  y = x.AppPerm(sigma)
  z = PrefixSum(y)
  return z

f = Share([1,0,1,1], 2)
v = Share([10, 20, 30, 40], 64)
g = Share([1,0,0,0,0,0,1,1,0,0,0], 2)
z = DynAccess(g, f, v)
z.print()

#endif

_ adjustlen(_ x, int n)
{
  _ ans;
  if (len(x) < n) {
    ans = _const(n-len(x), 0, order(x));
    _concat_(ans, x);
  } else if (len(x) > n) {
    ans = _slice(x, len(x)-n, len(x));
  } else {
    ans = _dup(x);
  }
  return ans;
}

_ DynAccess(_ g, _ f, _ v)
{
  int N = len(g);
  _ tau = StableSort2(f);
  _ sigma = StableSort2(g);
  _ vp = IfThen_b(f, v);
  _ w0 = AppInvPerm(vp, tau);
  //printf("w0 "); _print(w0);
  _ w = adjustlen(w0, N);
  _free(w0);
  _ x = Diff(w, 0);
  _ y = AppPerm(x, sigma);
  _ z = PrefixSum(y);
  _free(x); _free(y); _free(tau); _free(sigma); _free(vp); _free(w);
  return z;
}


#define StateAccess_dup DynAccess

_ StateAccess_mov(_ g, _ f, _ v)
{
  int N = len(g);
  if (N > 1) {
    printf("total send %ld\n", get_total_send());
    _ tau = StableSort2(f);
    printf("tau: total send %ld\n", get_total_send());
    _ sigma = StableSort2(g);
    printf("sigma: total send %ld\n", get_total_send());
    //printf("tau "); _print(tau);
    //printf("sigma "); _print(sigma);
    _ vp = IfThen_b(f, v);
    printf("vp: total send %ld\n", get_total_send());
    _ w0 = AppInvPerm(vp, tau);
    printf("w0: total send %ld\n", get_total_send());
    _ w = adjustlen(w0, N);
    printf("w: total send %ld\n", get_total_send());
    _free(w0);
    _ z = AppPerm(w, sigma);
    printf("z: total send %ld\n", get_total_send());
    _free(tau); _free(sigma); _free(vp); _free(w);
    return z;
  } else {
    _ vp = IfThen_b(f, v);
    _ z = sum(vp);
    _free(vp);
    return z;
  }
}

_ StateAccess_last(_ g, _ f, _ v)
{
  int N = len(g);
  int M = len(f);
  if (N > 1) {
  _ tau = StableSort2(f);
  _ sigma = StableSort2(g);
  _ vs = rshift(v, 0);
  _ vp = IfThen_b(f, vs);
  _ w0 = AppInvPerm(vp, tau);
  _ w = adjustlen(w0, N);
  _free(w0);
  _ x = lshift(w, share_getraw(v, M-1));
  _ z = AppPerm(x, sigma);
  _free(x); _free(tau); _free(sigma); _free(vs); _free(vp); _free(w);
  return z;
  } else {
    _ z = share_const(1,0,order(v));
    _setshare(z,0,v,M-1);
  return z;
  }
}

typedef struct {
  share_array v, phi, g, f;
} share_statefuldata;

share_statefuldata GroupBranch(share_statefuldata *x, _ sc)
{
  int n = len(x->v);
  int m = len(x->f);

  _ sphi = x->phi;
  _ sv = x->v;
  _ sg = x->g;
  _ sf = x->f;

  _ rho = GroupCountSort(sg, sc);
  _ sc1 = AppInvPerm(sc, rho);
  _ sc1neg = vneg(sc1);
  _ d = Diff(sc1,0);
  _ g_out = OR(sg,d);
  _ v_out = AppInvPerm(sv, rho);
  _ phi_out = AppInvPerm(sphi, rho);
  _ sr = StateAccess_last(sf, sg, sc1);
  _ l = StateAccess_mov(sf, sg, sc1neg);
  _ f_out = share_const(2*m, 0, 2);
  for (int i = 0; i < m; i++) {
        _setshare(f_out, 2*i, l, i);
        _setshare(f_out, 2*i+1, sr, i);
  }
  _free(rho); _free(sc1); _free(sc1neg); _free(d);
  _free(sr); _free(l); // _free(sphi); _free(sv); _free(sg); _free(sf); _free(sc);

  share_statefuldata tmp = {v_out, phi_out, g_out, f_out};
//  _free(v_out); _free(phi_out); _free(g_out); _free(f_out);
  return tmp;
}

_pair ANSV(_ sx)
{
  // parameter initialization
  int n = len(sx);
  int d = blog(n+1-1)+1;
  share_t q = 1 << d;

  // output data
  _ Lp = share_const(n, 0, q);
  _ Lv = share_const(n, 0, order(sx));

  // segment tree construction
  _ SegTree = share_const(2*n, 0, order(sx));
  for (int i=0; i<n; i++) {
    _setshare(SegTree, n+i, sx, i);
  }
  _ *Flag;
  NEWA(Flag, _, d+1);
  for (int i=0; i<d+1; i++) Flag[i] = share_const(n, 0, 2);

  int len = n;
  for (int i=d-1; i>0; i--){
    len = div(len,2).quot;
    _ Vlc = share_const(len, 0, order(sx));
    _ Vrc = share_const(len, 0, order(sx));
    for (int j=0; j<len; j++) {
      _setshare(Vlc, j, SegTree, 2*len+2*j);
      _setshare(Vrc, j, SegTree, 2*len+2*j+1);
    }
    _ cp = LessThan(Vlc, Vrc);
    _ Vmin = IfThenElse2(cp, Vlc, Vrc);
    for (int j=0; j<len; j++) {
      _setshare(SegTree, len+j, Vmin, j);
    }
    _ Vls = share_const((n >> 1), 0, order(sx));
    _ Vrx = share_const((n >> 1), 0, order(sx));
    _ Vps = share_const((n >> 1), 0, 2);
    int k = 0;
    for (int j=0; j<(n>>1); j++) {
      _setshare(Vls, j, Vlc, (j >> (-i+d-1)));
      while (div((k >> (-i+d-1)),2).rem == 0){
        k++;
      }
      _setshare(Vrx, j, sx, k);
      _setshare(Vps, j, Flag[i+1], k);
      k++;
    }
    _ Vb = LessThan(Vls, Vrx);
    _ Vp = OR(Vb, Vps);
    k = 0;
    for (int j=0; j<n; j++) {
      if (div(j>>(-i+d-1),2).rem == 1){
        _setshare(Flag[i], j, Vp, k);
        k++;
      } else {
        _setshare(Flag[i], j, Flag[i+1], j);
      }
    }
    _free(Vlc); _free(Vrc); _free(Vmin); _free(cp);
    _free(Vls); _free(Vrx); _free(Vps); _free(Vb); _free(Vp);
  }
  for (int i=1; i<d; i++){
    vadd_(Flag[i], Flag[i+1]);
  }

  //// print
  //_print(SegTree);
  //for (int i=1; i<d; i++){
  //  _print(Flag[i]);
  //}

  // top-down traversal
  // set initial state
  _ sv = share_const(n, 0, order(sx));
  _setshares(sv,0,n,sx,0);
  _ sphi = share_const(n, 0, q);
  for (int j = 0; j < n; j++) share_addpublic(sphi, j, j);
  _ sg = share_const(n, 0, 2);
  share_addpublic(sg, 0, 1);
  _ Vf = share_const(n, 0, 2);
  share_addpublic(Vf, 0, 1);
  _ sf = share_const(1, 0, 2);
  _setshares(sf,0,1,Vf,0);
  _ sc = share_const(n, 0, 2);
  _setshares(sc,0,n,Flag[1],0);
  for (int j = 0; j < n; j++) share_addpublic(sc, j, div((j >> (d-2)),2).rem);
  share_statefuldata tmp0 = {sv, sphi, sg, sf};
  share_statefuldata tmp = GroupBranch(&tmp0, sc);
  _ sca = B2A(sc,q);
  for (int j = 0; j < n; j++) share_mulpublic(sca, j, (1 << d-2));
  vadd_(Lp,sca);
  sv = tmp.v; sphi = tmp.phi; sg = tmp.g;
  _setshares(Vf,0,2,tmp.f,0);
  for (int i=1; i<d-1; i++){
    int len = 1 << i;
    _ sf = share_const(1<<i,0,2);
    _setshares(sf,0,1<<i,Vf,0);
    _ Vd = share_const(len, 0, order(sx));
    for (int j=0; j<len; j++) _setshare(Vd, j, SegTree, ((1<<(i+1))+(2*j+1)));
    _ Yd = StateAccess_dup(sg,sf,Vd);
    _ Va = LessThan(Yd, sv);
    _ st = share_const(n, 0, 2);
    _setshares(st,0,n,Flag[i+1],0);
    for (int j = 0; j < n; j++) share_addpublic(st, j, div(j >> (d-2-i),2).rem);
    _ Vb = AppPerm(st,sphi);
    _ Vh = share_const(n, 0, 2);
    for (int k=1; k<i+1; k++) vadd_(Vh, Flag[k]);
    _ sk = AppPerm(Vh,sphi);
    sc = IfThenElse2(sk, Va, Vb);
    share_statefuldata tmp0 = {sv, sphi, sg, sf};
    share_statefuldata tmp = GroupBranch(&tmp0, sc);
    AppInvPerm_(sc, sphi);
    sv = tmp.v; sphi = tmp.phi; sg = tmp.g;
    _setshares(Vf,0,1<<(i+1),tmp.f,0);
    sca = B2A(sc,q);
    for (int j = 0; j < n; j++) share_mulpublic(sca, j, (1 << d-2-i));
    vadd_(Lp,sca);
    _free(Vd); _free(Yd); _free(Va); _free(st); _free(Vb); _free(Vh); _free(sk);
  }
  _ Vw = StateAccess_dup(sg, Vf, sx);
  Lv = AppInvPerm(Vw, sphi);

  _free(sv); _free(sphi); _free(sg); _free(Vf); _free(sf); _free(sc); _free(sca);
  _free(Vw);

  _free(SegTree);
  for (int i=0; i<d+1; i++) {
    if (Flag[i] != NULL) {
      _free(Flag[i]);
    }
  }
  free(Flag);

  _pair out = {Lp, Lv};
  return out;
}
