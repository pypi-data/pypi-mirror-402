#ifndef _SHAMIRE_H
 #define _SHAMIRE_H

//#include "share.h"
#include "field.h"
//#include "func.h"
#include "precompute.h"

/****************************************************************************
 * Shamirのシェア (3 party)
 ****************************************************************************/

static share_array share_shamir_new_channel(int n, share_t q, share_t *A, int channel)
{
  int i;
  NEWT(share_array, ans);
  int k;

  ans->type = SHARE_T_SHAMIR;
  ans->irr_poly = 0;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > 3) return ans;

  ans->A = pa_new(n, k);
  if (_party <= 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    A3 = pa_new(n, k);
    pa_iter itr_A1 = pa_iter_new(A1);
    pa_iter itr_A2 = pa_iter_new(A2);
    pa_iter itr_A3 = pa_iter_new(A3);
    pa_iter itr_ans = pa_iter_new(ans->A);
    for (i=0; i<n; i++) {
      share_t r;
      pa_iter_set(itr_ans, A[i]);
      r = RANDOM0(q);
      //pa_set(A1, i, MOD(A[i] + r));
      //pa_set(A2, i, MOD(A[i] + 2*r));
      //pa_set(A3, i, MOD(A[i] + 3*r));
      pa_iter_set(itr_A1, MOD(A[i] + r));
      pa_iter_set(itr_A2, MOD(A[i] + 2*r));
      pa_iter_set(itr_A3, MOD(A[i] + 3*r));
    }
    pa_iter_flush(itr_A1);
    pa_iter_flush(itr_A2);
    pa_iter_flush(itr_A3);
    pa_iter_flush(itr_ans);
    mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
    mpc_send_pa_channel(TO_PARTY2, A2, channel);
    mpc_send_pa_channel(TO_PARTY3, A3, channel);

    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
  } else {
    mpc_recv_share_channel(FROM_SERVER, ans, channel);
  }

  return ans;
}
#define share_shamir_new(n, q, A) share_shamir_new_channel(n, q, A, 0)

static share_t GF_mul(share_t a, share_t b, share_t irr_poly);

static share_array share_shamir_GF_new_channel(int n, share_t q, share_t *A, share_t irr_poly, int channel)
{
  int i;
  NEWT(share_array, ans);
  int k;

  ans->type = SHARE_T_SHAMIR;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > 3) return ans;

  ans->A = pa_new(n, k);
  if (_party <= 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    A3 = pa_new(n, k);
    pa_iter itr_A1 = pa_iter_new(A1);
    pa_iter itr_A2 = pa_iter_new(A2);
    pa_iter itr_A3 = pa_iter_new(A3);
    pa_iter itr_ans = pa_iter_new(ans->A);
    for (i=0; i<n; i++) {
      share_t r;
      pa_iter_set(itr_ans, A[i]);
      r = RANDOM0(q);
      pa_iter_set(itr_A1, A[i] ^ GF_mul(1, r, irr_poly));
      pa_iter_set(itr_A2, A[i] ^ GF_mul(2, r, irr_poly));
      pa_iter_set(itr_A3, A[i] ^ GF_mul(3, r, irr_poly));
    }
    pa_iter_flush(itr_A1);
    pa_iter_flush(itr_A2);
    pa_iter_flush(itr_A3);
    pa_iter_flush(itr_ans);
    if (_party == 0) {
      mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
      mpc_send_pa_channel(TO_PARTY2, A2, channel);
      mpc_send_pa_channel(TO_PARTY3, A3, channel);
    }

    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
  } else {
    mpc_recv_share_channel(FROM_SERVER, ans, channel);
  }

  return ans;
}
#define shamir_GF_new(n, q, A, irr_poly) share_shamir_GF_new_channel(n, q, A, irr_poly, 0)
#define share_shamir_GF_new(n, q, A, irr_poly) share_shamir_GF_new_channel(n, q, A, irr_poly, 0)

static _s3 share_shamir3_xor_new_channel(int n, share_t q, share_t *A, int xor, int channel)
{
  int i;
  NEWT(share_array, ans);
  int k;

  //ans->type = SHARE_T_SHAMIR;
  ans->type = SHARE_T_33ADD;
  ans->irr_poly = q;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > 3) return ans;

  ans->A = pa_new(n, k);
  if (_party <= 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    A3 = pa_new(n, k);
    pa_iter itr_A1 = pa_iter_new(A1);
    pa_iter itr_A2 = pa_iter_new(A2);
    pa_iter itr_A3 = pa_iter_new(A3);
    pa_iter itr_ans = pa_iter_new(ans->A);
    for (i=0; i<n; i++) {
      share_t r1, r2, r3;
      pa_iter_set(itr_ans, A[i]);
      r1 = RANDOM0(q);
      r2 = RANDOM0(q);
      if (xor) {
        r3 = A[i] ^ r1 ^ r2;
      } else {
        r3 = MOD(A[i] - r1 - r2);
      }
      //pa_set(A1, i, r1);
      //pa_set(A2, i, r2);
      //pa_set(A3, i, r3);
      pa_iter_set(itr_A1, r1);
      pa_iter_set(itr_A2, r2);
      pa_iter_set(itr_A3, r3);
    }
    pa_iter_flush(itr_A1);
    pa_iter_flush(itr_A2);
    pa_iter_flush(itr_A3);
    pa_iter_flush(itr_ans);
    mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
    mpc_send_pa_channel(TO_PARTY2, A2, channel);
    mpc_send_pa_channel(TO_PARTY3, A3, channel);

    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
//  } else if (_party == 3) {
//    mpc_recv_share_channel(FROM_PARTY3, ans, channel);
  } else {
    mpc_recv_share_channel(FROM_SERVER, ans, channel);
  }

  return ans;
}
#define shamir3_xor_new(n, q, A) share_shamir3_xor_new_channel(n, q, A, 1, 0)
#define shamir3_new(n, q, A) share_shamir3_xor_new_channel(n, q, A, 0, 0)

/////////////////////////////////////////////////////////
// Shamirのシェアでの掛け算（ローカル）
/////////////////////////////////////////////////////////
_s3 vmul_shamir(_ x, _ y)
{
  if (_party > 3) return NULL;
  int n = len(x);
  if (n != len(y)) {
    printf("vmul_shamir: len(x)=%d len(y)=%d\n", n, len(y));
    exit(1);
  }

  _ ans;

  if (_party <= 0) {
    ans = vmul(x, y);
    ans->type = SHARE_T_33ADD;
    return ans;
  }

  share_t q = order(x);

  ans = _dup(x);
  // 並列化は容易
  for (int i=0; i<n; i++) {
    share_t t;
    if (_party == 1) t = MOD(3*pa_get(x->A, i)*pa_get(y->A, i));
    if (_party == 2) t = MOD(3*q - 3*pa_get(x->A, i)*pa_get(y->A, i));
    if (_party == 3) t = MOD(pa_get(x->A, i)*pa_get(y->A, i));
    pa_set(ans->A, i, t);
  }

  ans->type = SHARE_T_33ADD;
  return ans;
}

_s3 vmul_shamir_GF(_s x, _s y, share_t irr_poly)
{
  int n = len(x);
  if (n != len(y)) {
    printf("vmul_shamir_GF: len(x)=%d len(y)=%d\n", n, len(y));
    exit(1);
  }

  if (_party <= 0) {
  //  return vmul_GF(x, y, irr_poly); // !!!!!!
    _ ans = _dup(x);
    for (int i=0; i<n; i++) {
      share_t t;
      t = GF_mul(pa_get(x->A, i), pa_get(y->A, i), irr_poly);
      //printf("x %x y %x t %x\n", pa_get(x->A, i), pa_get(y->A, i), t);
      pa_set(ans->A, i, t);
    }
    ans->type = SHARE_T_33ADD;
    ans->irr_poly = irr_poly;
    return ans;
  }

  _ ans;
  share_t q = order(x);

  ans = _dup(x);
  // 並列化は容易
  for (int i=0; i<n; i++) {
    share_t t;
    if (_party == 1) t = GF_mul(pa_get(x->A, i), pa_get(y->A, i), irr_poly);
    if (_party == 2) t = GF_mul(pa_get(x->A, i), pa_get(y->A, i), irr_poly);
    if (_party == 3) t = GF_mul(pa_get(x->A, i), pa_get(y->A, i), irr_poly);
    pa_set(ans->A, i, t);
  }
  ans->type = SHARE_T_33ADD;
  ans->irr_poly = irr_poly;

  return ans;
}

///////////////////////////////////////////////////////
// 連続する step 個の要素の和を求める（ローカル）
///////////////////////////////////////////////////////
_ shamir_reduce(_ x, int step)
{
  int n = len(x);
  int m = n/step;
  if (m * step != n) {
    printf("shamir_reduce: n = %d step = %d\n", n, step);
    exit(1);
  }
  _ ans = _const_shamir(m, 0, order(x));
  //ans->type = x->type;
  // i に関する並列化は容易
  for (int i=0; i<m; i++) {
    for (int j=0; j<step; j++) {
      _addshare_shamir(ans, i, x, i*step+j);
    }
  }
  return ans;
}

////////////////////////////////////////////////////////////////////////////
// Shamirのシェア (3-party additive) を加法的シェア (2-party additive)に変換
////////////////////////////////////////////////////////////////////////////
_ shamir_convert_xor_channel(_s3 x, int xor, int channel)
{
  int n = len(x);

  if (_party <= 0) {
    _ ans = _dup(x);
    ans->type = SHARE_T_22ADD;
    return ans;
  }

  _ ans;
  share_t q = order(x);
  if (_party == 1 || _party == 2) {
    ans = _dup(x);
    ans->type = SHARE_T_22ADD;
    _ tmp = _dup(x);
    if (_party == 1) {
    //  unsigned long init[5];
    //  mpc_recv(TO_PARTY3, init, sizeof(init[0])*5);
    //  MT m3 = MT_init_by_array(init, 5);
      for (int i=0; i<n; i++) {
      //  share_t r = RANDOM(m3, q);
      //  share_t r = RANDOM(mt3[channel], q);
        share_t r = RANDOM(mt_[TO_PARTY3][channel], q);
        pa_set(tmp->A, i, r);
      }
    //  MT_free(m3);
    } else { // _party == 2
      mpc_recv_share_channel(FROM_PARTY3, tmp, channel);
      //printf("recv tmp "); _print(tmp);
    }
    if (xor) {
      _ tmp2 = vadd_GF(ans, tmp);
      _move_(ans, tmp2);
    } else {
      vadd_(ans, tmp);
    }
    _free(tmp);
  }
  if (_party == 3) {
  //  unsigned long init[5]={0x123, 0x234, 0x345, 0x456, 0};
  //  MT m3 = MT_init_by_array(init, 5);
    //_ a1 = share_dup(x);
    _ a2 = share_dup(x);
    for (int i=0; i<n; i++) {
      share_t t = pa_get(x->A, i);
    //  share_t r = RANDOM(m3, q);
    //  share_t r = RANDOM(mt3[channel], q);
      share_t r = RANDOM(mt_[1][channel], q);
      //pa_set(a1->A, i, r);
      if (xor) {
        pa_set(a2->A, i, t ^ r);
      } else {
        pa_set(a2->A, i, MOD(q+t-r));
      }
    }
    //printf("send a2 "); _print(a2);
    mpc_send_share_channel(TO_PARTY2, a2, channel);
    _free(a2);
    ans = NULL;
  }
  return ans;
}
#define shamir_convert_channel(x, channel) shamir_convert_xor_channel(x, 0, channel)
#define shamir_convert(x) shamir_convert_xor_channel(x, 0, 0)

/////////////////////////////////////////////////////////////
// 3 party の加法的シェアから生の値を求める
/////////////////////////////////////////////////////////////
#if 0
_ shamir3_reconstruct_xor_channel_old(_s3 x, int xor, int channel)
{
  if (_party <= 0) {
    return _dup(x);
  }

  int n = len(x);

  _ ans;
  share_t q = order(x);
  if (_party == 1) {
    mpc_send_share_channel(TO_PARTY2, x, channel);
  }
  if (_party == 3) {
    mpc_send_share_channel(TO_PARTY2, x, channel);
  }
  if (_party == 2) {
    _ from_party1 = _dup(x);
    _ from_party3 = _dup(x);
    mpc_recv_share_channel(FROM_PARTY3, from_party3, channel);
    mpc_recv_share_channel(FROM_PARTY1, from_party1, channel);
    _ to_party1, to_party3;
    if (xor) {
      to_party1 = vadd_shamir_GF(x, from_party3);
      to_party3 = vadd_shamir_GF(x, from_party1);
      ans = vadd_shamir_GF(to_party1, from_party1);
    } else {
      to_party1 = vadd(x, from_party3);
      to_party3 = vadd(x, from_party1);
      ans = vadd(to_party1, from_party1);
    }
    mpc_send_share_channel(TO_PARTY3, to_party3, channel);
    mpc_send_share_channel(TO_PARTY1, to_party1, channel);
    _free(from_party1); _free(from_party3);
    _free(to_party1); _free(to_party3);
  }
  if (_party == 1) {
    _ from_party2 = _dup(x);
    mpc_recv_share_channel(FROM_PARTY2, from_party2, channel);
    if (xor) {
      ans = vadd_shamir_GF(x, from_party2);
    } else {
      ans = vadd(x, from_party2);
    }
    _free(from_party2);
  }
  if (_party == 3) {
    _ from_party2 = _dup(x);
    mpc_recv_share_channel(FROM_PARTY2, from_party2, channel);
    if (xor) {
      ans = vadd_shamir_GF(x, from_party2);
    } else {
      ans = vadd(x, from_party2);
    }
    _free(from_party2);
  }
  return ans;
}
#endif

/////////////////////////////////////////////////////////////
// 3 party の加法的シェアから生の値を求める
/////////////////////////////////////////////////////////////
_ shamir3_reconstruct_xor_channel(_s3 x, int xor, int channel)
{
  if (_party > 3) return NULL;

  if (x->type != SHARE_T_33ADD) {
    printf("shamir3_reconstruct: type = %d\n", x->type);
  }
  _ ans;
  if (_party <= 0) {
    ans = _dup(x);
    ans->type = SHARE_T_RAW;
    return ans;
  }



  int n = len(x);

  share_t q = order(x);
  if (_party == 2) {
    _ from_party1 = _dup(x);
    _ from_party3 = _dup(x);
    mpc_recv_share_channel(FROM_PARTY1, from_party1, channel);
    mpc_recv_share_channel(FROM_PARTY3, from_party3, channel);
    _ to_party1, to_party3;
    if (xor) {
      _ tmp = vadd_shamir_GF(x, from_party3);
      ans = vadd_shamir_GF(tmp, from_party1);
      _free(tmp);
    } else {
      //_ tmp = smul(2, from_party1);
      //ans = vsub(tmp, x);
      _ tmp = vadd(x, from_party1);
      ans = vadd(tmp, from_party3);
      _free(tmp);
    }
    mpc_send_share_channel(TO_PARTY1, ans, channel);
    mpc_send_share_channel(TO_PARTY3, ans, channel);
    _free(from_party1); _free(from_party3);
  } else {
    mpc_send_share_channel(TO_PARTY2, x, channel);
    ans = _dup(x);
    mpc_recv_share_channel(FROM_PARTY2, ans, channel);
  }

  //_sync3();
  //printf("sync ok");


  ans->type = SHARE_T_RAW;
  return ans;
}
#define shamir3_reconstruct_channel(x, channel) shamir3_reconstruct_xor_channel(x, 0, channel)
#define shamir3_reconstruct_xor(x, xor) shamir3_reconstruct_xor_channel(x, xor, 0)
#define shamir3_reconstruct(x) shamir3_reconstruct_xor_channel(x, 0, 0)


/////////////////////////////////////////////////////////////
// Shamirのシェアから生の値を求める
/////////////////////////////////////////////////////////////
_ shamir_reconstruct_xor_channel(_s x, int xor, int channel)
{
  if (_party > 3) return NULL;

  if (x->type != SHARE_T_SHAMIR) {
    printf("shamir_reconstruct: type = %d\n", x->type);
  }
  _ ans;
  if (_party <= 0) {
    ans = _dup(x);
    ans->type = SHARE_T_RAW;
    return ans;
  }

  int n = len(x);

  share_t q = order(x);
  if (_party == 2) {
    _ from_party1 = _dup(x);
    mpc_recv_share_channel(FROM_PARTY1, from_party1, channel);
    _ from_party3;
    if (xor) {
      from_party3 = _dup(x);
      mpc_recv_share_channel(FROM_PARTY3, from_party3, channel);
    }
    _ tmp;
    if (xor) {
      tmp = vadd_shamir_GF(x, from_party3);
      ans = vadd_shamir_GF(tmp, from_party1);
    } else {
      tmp = smul(2, from_party1);
      ans = vsub(tmp, x);
    }
    _free(tmp);
    mpc_send_share_channel(TO_PARTY1, ans, channel);
    mpc_send_share_channel(TO_PARTY3, ans, channel);
  } else if (_party == 1) {
    mpc_send_share_channel(TO_PARTY2, x, channel);
    ans = _dup(x);
    mpc_recv_share_channel(FROM_PARTY2, ans, channel);
  } else { // _party == 3
    if (xor) {
      mpc_send_share_channel(TO_PARTY2, x, channel);
    }
    ans = _dup(x);
    mpc_recv_share_channel(FROM_PARTY2, ans, channel);
  }
  ans->type = SHARE_T_RAW;
  return ans;
}
#define shamir_reconstruct(x) shamir_reconstruct_xor_channel(x, 0, 0)
#define shamir_reconstruct_xor(x, xor) shamir_reconstruct_xor_channel(x, xor, 0)


/////////////////////////////////////////////////////////////
// 3 party の加法的シェアから Shamir のシェアに戻す
/////////////////////////////////////////////////////////////
#if 0
void shamir3_revert_precomp_M(int n, share_t q, share_t irr_poly, share_t *M, char *fname)
{
  if (_party > 0) goto sync;

  int degree;
  if (irr_poly) {
    degree = blog(irr_poly);
    q = 1 << degree;
  }


  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);
  char *fname3 = precomp_fname(fname, 3);

//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
//  unsigned long init3[5]={0x123, 0x234, 0x345, 0x456, 3};
  unsigned long *init3 = MT_init[3];
  MT m3 = MT_init_by_array(init3, 5);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 0};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);

  _ b[3];
  for (int p=0; p<3; p++) {
    b[p] = _const(n, 0, q);
  }
  _ r = _const(n, 0, q);
  for (int i=0; i<n; i++) {
    pa_set(b[1]->A, i, RANDOM(m1, q));
    pa_set(b[2]->A, i, RANDOM(m2, q));
    pa_set(b[0]->A, i, RANDOM(m3, q));
    pa_set(r->A,    i, RANDOM(m0, q));
  }
  _ bb = _const(n, 0, q);
  for (int i=0; i<n; i++) {
    share_t x;
    x = 0;
    for (int p=0; p<3; p++) {
      share_t y = pa_get(b[p]->A, i);
      if (irr_poly) {
        x = x ^ y;
      } else {
        x = MOD(x + y);
      }
    }
    pa_set(bb->A, i, x);
  }

  for (int i=0; i<n; i++) {
    share_t x = pa_get(bb->A, i);
    share_t z = pa_get(r->A, i);
    share_t y1, y2, y3;
    if (irr_poly) {
      if (M) {
        y1 = GF_mul(M[0], z, irr_poly) ^ x;
        y2 = GF_mul(M[1], z, irr_poly) ^ x;
        y3 = GF_mul(M[2], z, irr_poly) ^ x;
      } else {
        y1 = GF_mul(1, z, irr_poly) ^ x;
        y2 = GF_mul(2, z, irr_poly) ^ x;
        y3 = GF_mul(3, z, irr_poly) ^ x;
      }
    } else {
      y1 = MOD(1*z - x);
      y2 = MOD(2*z - x);
      y3 = MOD(3*z - x);
    }
    pa_set(b[1]->A, i, y1);
    pa_set(b[2]->A, i, y2);
    pa_set(b[0]->A, i, y3);
  }
  MT_free(m1);
  MT_free(m2);
  MT_free(m3);
  MT_free(m0);

  FILE *f0, *f1, *f2, *f3;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  f3 = fopen(fname3, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f3, n, q, init3);
  precomp_write_seed(f0, n, q, init1); // 使わない? ⇒　必要

  precomp_write_share(f1, b[1]);
  precomp_write_share(f2, b[2]);
  precomp_write_share(f3, b[0]);

  _ t0 = _const(n, 0, q);
  precomp_write_share(f0, t0); // 使わない? ⇒　必要
  _free(t0);

  _free(r);  _free(bb);
  _free(b[0]);  _free(b[1]);  _free(b[2]);

  fclose(f0);
  fclose(f1);
  fclose(f2);
  fclose(f3);

  free(fname0);  free(fname1);  free(fname2);  free(fname3);

sync:;

}
#endif
void shamir3_revert_precomp(int n, share_t q, share_t irr_poly, char *fname)
{
  if (_party > 0) goto sync;

  int degree;
  if (irr_poly) {
    degree = blog(irr_poly);
    q = 1 << degree;
  }


  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);
  char *fname3 = precomp_fname(fname, 3);

//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
//  unsigned long init3[5]={0x123, 0x234, 0x345, 0x456, 3};
  unsigned long *init3 = MT_init[3];
  MT m3 = MT_init_by_array(init3, 5);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 0};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);

  _ b[3];
  for (int p=0; p<3; p++) {
    b[p] = _const(n, 0, q);
  }
  _ r = _const(n, 0, q);
  for (int i=0; i<n; i++) {
    pa_set(b[1]->A, i, RANDOM(m1, q));
    pa_set(b[2]->A, i, RANDOM(m2, q));
    pa_set(b[0]->A, i, RANDOM(m3, q));
    pa_set(r->A,    i, RANDOM(m0, q));
  }
  _ bb = _const(n, 0, q);
  for (int i=0; i<n; i++) {
    share_t x;
    x = 0;
    for (int p=0; p<3; p++) {
      share_t y = pa_get(b[p]->A, i);
      if (irr_poly) {
        x = x ^ y;
      } else {
        x = MOD(x + y);
      }
    }
    pa_set(bb->A, i, x);
  }

  for (int i=0; i<n; i++) {
    share_t x = pa_get(bb->A, i);
    share_t z = pa_get(r->A, i);
    share_t y1, y2, y3;
    if (irr_poly) {
      y1 = GF_mul(1, z, irr_poly) ^ x;
      y2 = GF_mul(2, z, irr_poly) ^ x;
      y3 = GF_mul(3, z, irr_poly) ^ x;
    } else {
      y1 = MOD(1*z - x);
      y2 = MOD(2*z - x);
      y3 = MOD(3*z - x);
    }
    pa_set(b[1]->A, i, y1);
    pa_set(b[2]->A, i, y2);
    pa_set(b[0]->A, i, y3);
  }
  MT_free(m1);
  MT_free(m2);
  MT_free(m3);
  MT_free(m0);

  FILE *f0, *f1, *f2, *f3;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  f3 = fopen(fname3, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f3, n, q, init3);
  precomp_write_seed(f0, n, q, init1); // 使わない? ⇒　必要

  precomp_write_share(f1, b[1]);
  precomp_write_share(f2, b[2]);
  precomp_write_share(f3, b[0]);

  _ t0 = _const(n, 0, q);
  precomp_write_share(f0, t0); // 使わない? ⇒　必要
  _free(t0);

  _free(r);  _free(bb);
  _free(b[0]);  _free(b[1]);  _free(b[2]);

  fclose(f0);
  fclose(f1);
  fclose(f2);
  fclose(f3);

  free(fname0);  free(fname1);  free(fname2);  free(fname3);

sync:;

}

#include "func.h"


///////////////////////////////////////////////////////////////////////////
// 33 Additive から Shamir のシェアを作る
///////////////////////////////////////////////////////////////////////////
_sx shamir3_revert_xor_channel(_s3x x, share_t irr_poly, int channel)
{
//  if (_party <= 0) {
//    return _dup(x);
//  }

//  if (x->type != SHARE_T_33ADD && x->type != SHARE_T_33XOR) {
//    printf("shamir3_revert: type = %d\n", x->type); // 本当はチェックすべき
//  }

  _ ans;
  if (_party < 0) {
    ans = _dup(x);
    ans->type = SHARE_T_SHAMIR;
    ans->irr_poly = irr_poly;
    return ans;
  }

  int n = len(x);

  int d = blog(irr_poly);
//  precomp_tables T = PRE_RE_tbl[d-1][channel];
  precomp_tables T = precomp_tbl_list_search(PRE_RE_tbl[channel], d, irr_poly);

  share_t q = order(x);

  if (T) {
    if (_party == 0) {
      ans = _dup(x);
      ans->type = SHARE_T_SHAMIR;
      ans->irr_poly = irr_poly;
      return ans;
    }
    _ b, r;
    b = _const(n, 0, q);
    r = _const(n, 0, q);
    for (int i=0; i<n; i++) {
      pa_set(b->A, i, precomp_get(T->TR));
      pa_set(r->A, i, precomp_get(T->Tt));
    }
  //  printf("b "); _print(b);
  //  printf("r "); _print(r);
    _ y;
    if (irr_poly) {
      y = vadd_shamir_GF(x, b);
    } else {
      y = vadd(x, b);
    }
    _ w = shamir3_reconstruct_xor_channel(y, irr_poly, channel);
    _ z;
    if (irr_poly) {
      z = vadd_shamir_GF(w, r);
    } else {
      z = vadd(w, r);
    }
    _free(b);  _free(r);  _free(w);  _free(y);
    z->type = SHARE_T_SHAMIR;
    z->irr_poly = irr_poly;
    return z;
  } else {
    if (_party == 0) {
      _ b[3];
      for (int p=0; p<3; p++) {
        b[p] = share_const_type(n, 0, q, SHARE_T_SHAMIR);
        for (int i=0; i<n; i++) {
          pa_set(b[p]->A, i, RANDOM0(q));
        }
      }
      mpc_send_share_channel(TO_PARTY1, b[1], channel);
      mpc_send_share_channel(TO_PARTY2, b[2], channel);
      mpc_send_share_channel(TO_PARTY3, b[0], channel);
      _ r = _const(n, 0, q);
      for (int i=0; i<n; i++) {
        pa_set(r->A, i, RANDOM0(q));
      }
      _ bb = _const(n, 0, q);
      for (int i=0; i<n; i++) {
        share_t x;
        x = 0;
        for (int p=0; p<3; p++) {
          share_t y = pa_get(b[p]->A, i);
          if (irr_poly) {
            x = x ^ y;
          } else {
            x = MOD(x + y);
          }
        }
        pa_set(bb->A, i, x);
      }
      for (int i=0; i<n; i++) {
        share_t x = pa_get(bb->A, i);
        share_t z = pa_get(r->A, i);
        share_t y1, y2, y3;
        if (irr_poly) {
          y1 = GF_mul(1, z, irr_poly) ^ x;
          y2 = GF_mul(2, z, irr_poly) ^ x;
          y3 = GF_mul(3, z, irr_poly) ^ x;
        } else {
          y1 = MOD(1*z - x);
          y2 = MOD(2*z - x);
          y3 = MOD(3*z - x);
        }
        pa_set(b[1]->A, i, y1);
        pa_set(b[2]->A, i, y2);
        pa_set(b[0]->A, i, y3);
      }
      mpc_send_share_channel(TO_PARTY1, b[1], channel);
      mpc_send_share_channel(TO_PARTY2, b[2], channel);
      mpc_send_share_channel(TO_PARTY3, b[0], channel);
      _free(r);  _free(bb);
      _free(b[0]);  _free(b[1]);  _free(b[2]);
      ans = _dup(x);
      ans->type = SHARE_T_SHAMIR;
      ans->irr_poly = irr_poly;
      return ans;
    } else {
      _ b, r;
      b = share_const_type(n, 0, q, SHARE_T_SHAMIR);
      r = share_const_type(n, 0, q, SHARE_T_SHAMIR);
      mpc_recv_share_channel(FROM_SERVER, b, channel);
      mpc_recv_share_channel(FROM_SERVER, r, channel);
      _ y;
      if (irr_poly) {
        y = vadd_shamir_GF(x, b);
      } else {
        y = vadd(x, b);
      }
      _ w = shamir3_reconstruct_xor_channel(y, irr_poly, channel);
      w->type = SHARE_T_SHAMIR;
      if (irr_poly) {
        ans = vadd_shamir_GF(w, r);
      } else {
        ans = vadd(w, r);
      }
      _free(b);  _free(r);  _free(w);  _free(y);
      ans->type = SHARE_T_SHAMIR;
      ans->irr_poly = irr_poly;
      return ans;
    }
  }

}
#define shamir3_revert_channel(x, channel) shamir3_revert_xor_channel(x, 0, channel)
#define shamir3_revert_xor(x, irr_poly) shamir3_revert_xor_channel(x, irr_poly, 0)
#define shamir3_revert(x) shamir3_revert_xor_channel(x, 0, 0)

static void share_check_shamir(share_array a, share_t irr_poly)
{
  if (_party > 3) return; // 要検討
  if (a->type != SHARE_T_SHAMIR) {
    printf("share_check_shamir: type = %d\n", a->type);
  }
  int i, n;
//  comm c0, c1, c2;
  share_t q;

//  printf("share_check\n");
  n = a->n;
  q = a->q;
  int k = blog(q-1)+1;
//  printf("share_check q=%d k=%d w=%d\n", q, k, a->A->w);
  int err=0;
  if (_party <= 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    A3 = pa_new(n, k);
    printf("check party %d: ", _party);
    mpc_recv_pa(FROM_PARTY1, A1);
    mpc_recv_pa(FROM_PARTY2, A2);
    mpc_recv_pa(FROM_PARTY3, A3);
    if (_party == 0) {
      for (i=0; i<n; i++) {
        share_t x, r1, r2;
        if (irr_poly) {
          x = pa_get(A1, i) ^ pa_get(A2, i) ^ pa_get(A3, i); 
          if ((u64)x != pa_get(a->A, i)){
            printf("share_check_shamir: i = %d A = %d %d A1 = %d A2 = %d A3 = %d\n", i, (int)pa_get(a->A, i), (int)x, (int)pa_get(A1,i), (int)pa_get(A2,i), (int)pa_get(A3,i));
            err=1;
          }
        } else {
          r1 = MOD(pa_get(A2, i) - pa_get(A1, i)); 
          r2 = MOD(pa_get(A3, i) - pa_get(A2, i)); 
          x = MOD(pa_get(A1, i) - r1);
          if ((u64)x != pa_get(a->A, i) || r1 != r2) {
            printf("share_check_shamir: i = %d A = %d %d A1 = %d A2 = %d A3 = %d\n", i, (int)pa_get(a->A, i), (int)x, (int)pa_get(A1,i), (int)pa_get(A2,i), (int)pa_get(A3,i));
            err=1;
          }
        }
      }
      printf("check done\n");
    }
    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
  } else {
    printf("check party %d: \n", _party);
    mpc_send_share(TO_SERVER, a);
  }
  //if (err) exit(1);
}
#define _check_shamir share_check_shamir


static void share_check_shamir3(share_array a, share_t irr_poly)
{
//  if (_party >  2) return; // 要検討
  if (a->type != SHARE_T_33ADD) {
    printf("share_check_shamir3: type = %d\n", a->type);
  }
  int i, n;
//  comm c0, c1, c2;
  share_t q;

//  printf("share_check\n");
  n = a->n;
  q = a->q;
  int k = blog(q-1)+1;
//  printf("share_check q=%d k=%d w=%d\n", q, k, a->A->w);
  int err=0;
  if (_party <= 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    A3 = pa_new(n, k);
    printf("check party %d: ", _party);
    if (_party == 0) {
      mpc_recv_pa(FROM_PARTY1, A1);
      mpc_recv_pa(FROM_PARTY2, A2);
      mpc_recv_pa(FROM_PARTY3, A3);
      //printf("A1 "); pa_print(A1);
      //printf("A2 "); pa_print(A2);
      //printf("A3 "); pa_print(A3);
      //printf("A "); pa_print(a->A);
      for (i=0; i<n; i++) {
        share_t x;
        if (irr_poly) {
          x = pa_get(A1, i) ^ pa_get(A2, i) ^ pa_get(A3, i); 
        } else {
          x = MOD(pa_get(A1, i) + pa_get(A2, i) + pa_get(A3, i));
        }
        if ((u64)x != pa_get(a->A, i)){
          printf("share_check_shamir3: i = %d A = %d %d A1 = %d A2 = %d A3 = %d\n", i, (int)pa_get(a->A, i), (int)x, (int)pa_get(A1,i), (int)pa_get(A2,i), (int)pa_get(A3,i));
          err=1;
          //exit(1);
        }
      }
      printf("check done\n");
    }
    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
  } else {
    printf("check party %d: \n", _party);
    mpc_send_share(TO_SERVER, a);
  }
}
#define _check_shamir3 share_check_shamir3

void _print_debug_shamir(_s x, share_t irr_poly)
{
  _ tmp = shamir_reconstruct_xor(x, irr_poly);
  _print(tmp);
  _check_shamir(x, irr_poly);
  _free(tmp);
}

void _print_debug_shamir3(_s3 x, share_t irr_poly)
{
  _ tmp = shamir3_reconstruct_xor(x, irr_poly);
  _print(tmp);
  _check_shamir3(x, irr_poly);
  _free(tmp);
}

///////////////////////////////////////////////////////////////////////////////////////
// one-hot vector
// 入力: (2,2)-additive
// 出力: (2,3)-Shamir (additive)
///////////////////////////////////////////////////////////////////////////////////////
_ onehotvec_shamir_table_channel(int b, _ x, share_t q, precomp_tables T, int channel)
{
  int n = len(x);
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  _ ans = _const_shamir(n*w, 0, q);
  //ans->type = SHARE_T_SHAMIR;

  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      for (int j=0; j<w; j++) {
      //  pa_set(ans->A, p*w+j, pa_get(T->Tt->u.share.a, xx*w + j)%q);
        int z = (xx == j);
        pa_set(ans->A, p*w+j, z % q);
      }
    }
    return ans;
  }

  if (T == NULL) {
    printf("onehotvec_shamir_table_channel: T = %p\n", T);
    exit(1);
  }

  if (_party == 1 || _party == 2) {
    // 表の値を求める（疑似乱数の場合もあるので並列化は注意）
    _ t = _const(n*w, 0, q);
    for (int p=0; p<n*w; p++) {
      pa_set(t->A, p, precomp_get(T->Tt)%q);
    }

    // x のシェアを乱数でマスクする（並列化は容易）
    _ y = _const(n, 0, k);
    for (int p=0; p<n; p++) {
      share_t tt, tx, t;
      tt = precomp_get(T->TR) & (k-1);
      tx = pa_get(x->A, p) & (k-1);
      t = k - tt + tx;
      //printf("tt %d tx %d t %d\n", tt, tx, t);
    //  pa_set(y->A, p, (k - precomp_get(T->TR) + pa_get(x->A, p))%k);
      pa_set(y->A, p, (k - tt + tx)%k);
    }

    // y を reveal したものを z とする
    _ z = _const(n, 0, k);
    mpc_exchange_share_channel(y, z, channel);
    // 表を引いて one hot vector を求める（並列化は容易）
    for (int p=0; p<n; p++) {
      share_t xr = pa_get(y->A, p);
      share_t ys = pa_get(z->A, p);
      share_t tt;
      tt = (xr + ys) % k;
      for (int j=0; j<w; j++) {
      //  pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + tt*w + j)%q);
        share_t z;
        z = (k + j - tt) % k;
        pa_set(ans->A, p*w+j, pa_get(t->A, p*w + z)%q);
      }
      if (_party == 1) pa_set(y->A, p, tt);
    }
    if (_party == 1) {
      //printf("send y to party 3\n"); _print(y);
      mpc_send_share_channel(TO_PARTY3, y, channel); // y+z を送る
    }
    _free(y);  _free(z);  _free(t);
  }
  if (_party == 3) {
    _ t = _const_shamir(n*w, 0, q);
    for (int p=0; p<n*w; p++) {
      //pa_set(t->A, p, precomp_get(T->Tt)%q);
      pa_set(t->A, p, precomp_get(T->Tt)&(q-1));
    }

    _ y = _const_shamir(n, 0, k);
    //printf("recv y\n"); _print(y);
    mpc_recv_share_channel(FROM_PARTY1, y, channel);
    //printf("recv y\n"); _print(y);

    // 表を引いて one hot vector を求める（並列化は容易）
    for (int p=0; p<n; p++) {
      share_t xr = pa_get(y->A, p);
      //share_t ys = pa_get(z->A, p);
      share_t tt;
      //tt = (xr + ys) % k;
      tt = xr;
      for (int j=0; j<w; j++) {
      //  pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + tt*w + j)%q);
        share_t z = (k + j - tt) % k;
        pa_set(ans->A, p*w+j, pa_get(t->A, p*w + z)%q);
      }
    }
    _free(y);  
    //_free(z);  
    _free(t);
  }

  return ans;
}
#define onehotvec_shamir_table(b, x, q, T) onehotvec_shamir_table_channel(b, x, q, T, 0)

static share_t GF_mul(share_t a, share_t b, share_t irr_poly);

void onehotvec_shamir3_type_precomp(int b, int n, share_t q, share_t irr_poly, int type, char *fname)
{
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  if (_party > 0) goto sync;

  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);
  char *fname3 = precomp_fname(fname, 3);

  int n2 = n;
  if (type == SHARE_T_RSS) n2 = 2*n;

  share_t *func_table;
  NEWA(func_table, share_t, k*w);
  for (int i=0; i<k; i++) {
    for (int j=0; j<w; j++) {
      func_table[i*w+j] = 0; 
    }
    func_table[i*w+i] = 1;
  }

  _ F = _const(n2*k*w, 0, q); // n で良い?
  // x1, x2, x3 のmask用の乱数
  _ R = _const(n, 0, k);
  _ S = _const(n, 0, k);
  _ T = _const(n, 0, k);
//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
//  unsigned long init3[5]={0x123, 0x234, 0x345, 0x456, 3};
  unsigned long *init3 = MT_init[3];
  MT m3 = MT_init_by_array(init3, 5);
  for (int p=0; p<n; p++) {
    share_t r = RANDOM(m1, k);
    share_t s = RANDOM(m2, k);
    share_t t = RANDOM(m3, k);
    share_t u;
    //r = s = t = 0; // test
    if (irr_poly) {
      u = (r ^ s ^ t);
    } else {
      u = (r + s + t) % k;
    }
    pa_set(R->A, p, r);
    pa_set(S->A, p, s);
    pa_set(T->A, p, t);
    for (int i=0; i<k; i++) {
      for (int j=0; j<w; j++) {
        if (irr_poly) {
          pa_set(F->A, p*k*w + i*w + j, func_table[(i^u)*w + j]); //  xor で無くても良い?
        } else {
          pa_set(F->A, p*k*w + i*w + j, func_table[((i+u)%k)*w + j]);
        }
      }
    }
  }
  MT_free(m1);
  MT_free(m2);
  MT_free(m3);
  //printf("R "); _print(R);
  //printf("S "); _print(S);

  FILE *f0, *f1, *f2, *f3;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  f3 = fopen(fname3, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f3, n, q, init3);
  precomp_write_seed(f0, n, q, init1); // 使わない?



  _ t1 = _const(n2*k*w, 0, q);
  _ t2 = _const(n2*k*w, 0, q);
  _ t3 = _const(n2*k*w, 0, q);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);
  for (int p=0; p<n; p++) {
    for (int i=0; i<k; i++) {
      for (int j=0; j<w; j++) {
        share_t rr = RANDOM(m0, q);
        //rr = 0; // test
        share_t x = pa_get(F->A, p*k*w + i*w + j);
        if (type == SHARE_T_SHAMIR) {
          if (irr_poly) {
            pa_set(t1->A, p*k*w + i*w + j, GF_mul(1, rr, irr_poly) ^ x);
            pa_set(t2->A, p*k*w + i*w + j, GF_mul(2, rr, irr_poly) ^ x);
            pa_set(t3->A, p*k*w + i*w + j, GF_mul(3, rr, irr_poly) ^ x);
          } else {
            pa_set(t1->A, p*k*w + i*w + j, MOD(x + 1 * rr));
            pa_set(t2->A, p*k*w + i*w + j, MOD(x + 2 * rr));
            pa_set(t3->A, p*k*w + i*w + j, MOD(x + 3 * rr));
          }
        } else if (type == SHARE_T_RSS) {
          share_t ss = RANDOM(m0, q);
          //ss = 4; // test
          share_t tt;
          if (irr_poly) {
            tt = rr ^ ss;
            pa_set(t1->A, p*k*w + i*w + j, x ^ rr);
            pa_set(t2->A, p*k*w + i*w + j,     ss);
            pa_set(t3->A, p*k*w + i*w + j,     tt);
            pa_set(t1->A, p*k*w + i*w + j + n*k*w,     ss);
            pa_set(t2->A, p*k*w + i*w + j + n*k*w,     tt);
            pa_set(t3->A, p*k*w + i*w + j + n*k*w, x ^ rr);
          } else {
            tt = MOD(q*2 - rr - ss);
            pa_set(t1->A, p*k*w + i*w + j, MOD(x + rr));
            pa_set(t2->A, p*k*w + i*w + j, MOD(0 + ss));
            pa_set(t3->A, p*k*w + i*w + j, MOD(0 + tt));
            pa_set(t1->A, p*k*w + i*w + j + n*k*w, MOD(0 + ss));
            pa_set(t2->A, p*k*w + i*w + j + n*k*w, MOD(0 + tt));
            pa_set(t3->A, p*k*w + i*w + j + n*k*w, MOD(x + rr));
          }
        } else {
          printf("onehotvec_shamir3 precomp type = %d\n", type);
        }
      }
    }
  }
  MT_free(m0);
  precomp_write_share(f1, t1);
  precomp_write_share(f2, t2);
  precomp_write_share(f3, t3);

// P0 は table をそのまま格納
  _ t0 = _const(k*w, 0, q);
  for (int i=0; i<k; i++) {
    for (int j=0; j<w; j++) {
      pa_set(t0->A, i*w+j, func_table[i*w+j]);
    }
  }
  precomp_write_share(f0, t0);

  fclose(f0);
  fclose(f1);
  fclose(f2);
  fclose(f3);

  _free(F);  _free(R);  _free(S);  _free(T);
  _free(t0);  _free(t1);  _free(t2);  _free(t3);
  free(fname0);  free(fname1);  free(fname2);  free(fname3);
  free(func_table);

sync:;

}
#define onehotvec_shamir3_precomp(b, n, q, irr_poly, fname) onehotvec_shamir3_type_precomp(b, n, q, irr_poly, SHARE_T_SHAMIR,fname)


//_ shamir3_reconstruct_xor_channel(_ x, int xor, int channel);

_ onehotvec_shamir3_type_table_channel(int b, _s3 x, share_t q, share_t irr_poly, int type, precomp_tables T, int channel)
{
  int n = len(x);
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  int n2 = n;
  if (type == SHARE_T_RSS) n2 = 2*n;

  _ ans = share_const_type(n2*w, 0, q, type);

  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      for (int j=0; j<w; j++) {
        pa_set(ans->A, p*w+j, pa_get(T->Tt->u.share.a, xx*w + j)%q);
      }
    }
    return ans;
  }

  // 表の値を求める（疑似乱数の場合もあるので並列化は注意）
  _ t = share_const_type(n*k*w, 0, q, SHARE_T_33ADD);
  for (int p=0; p<n*k*w; p++) {
    pa_set(t->A, p, precomp_get(T->Tt)%q);
  }

  // x のシェアを乱数でマスクする（並列化は容易）
  _ y = share_const_type(n, 0, k, SHARE_T_33ADD);
  for (int p=0; p<n; p++) {
    if (irr_poly) {
      pa_set(y->A, p, (precomp_get(T->TR) ^ pa_get(x->A, p))%k);
    //  pa_set(y->A, p, (0 ^ pa_get(x->A, p))%k);
    } else {
      pa_set(y->A, p, (k - precomp_get(T->TR) + pa_get(x->A, p))%k);
    }
  }
//  printf("onehot y "); _print(y);

  // y を reveal したものを z とする
  _ z = shamir3_reconstruct_xor_channel(y, irr_poly, channel);
//  printf("onehot z "); _print(z);
  // 表を引いて one hot vector を求める（並列化は容易）
  for (int p=0; p<n; p++) {
    share_t xr = pa_get(z->A, p);
    for (int j=0; j<w; j++) {
      pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + xr*w + j)%q);
    }
  }
  _free(y);  _free(z);  _free(t);
//  printf("onehot ans "); _print(ans);

  return ans;
}
#define onehotvec_shamir3_table(b, x, q, irr_poly, T) onehotvec_shamir3_table_channel(b, x, q, irr_poly, T, 0)
#define onehotvec_shamir3_table_channel(b, x, q, irr_poly, T, channel) onehotvec_shamir3_type_table_channel(b, x, q, irr_poly, SHARE_T_RSS, T, channel)

///////////////////////////////////////////////////////////////////////////////////////////
// One-hot vector
// 入力 x: 33ADD
// 出力:   SHAMIR or RSS
///////////////////////////////////////////////////////////////////////////////////////////
_ onehotvec_shamir3_type_online_channel(_ x, share_t q, share_t irr_poly, int type, int channel)
{
  if (_party > 3) return NULL;
  //printf("onehotvec_shamir3_type_online_channel\n");
  if (type != SHARE_T_SHAMIR && type != SHARE_T_RSS) {
    printf("onehotvec_shamir3_type_online_channel: type = %d\n", type);
  }
  int n = x->n;
  int b = blog(order(x)-1)+1;
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  _ R = NULL, t = NULL;
  share_t *func_table;

  int n2 = n;
  if (type == SHARE_T_RSS) n2 = 2*n;

// 前計算
  if (_party <= 0) {
    // P1, P2, P3 用の表の計算

    NEWA(func_table, share_t, k*w);
    for (int i=0; i<k; i++) {
      for (int j=0; j<w; j++) {
        func_table[i*w+j] = 0; 
      }
      func_table[i*w+i] = 1;
    }

    _ F = _const(n2*k*w, 0, q);
    // x1, x2, x3 のmask用の乱数
    _ R = share_const_type(n, 0, k, type); // n で良い?
    _ S = share_const_type(n, 0, k, type);
    _ T = share_const_type(n, 0, k, type);
  //  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  //  MT m1 = MT_init_by_array(init1, 5);
    MT m1 = MT_init_by_array(MT_init[1], 5);
  //  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  //  MT m2 = MT_init_by_array(init2, 5);
    MT m2 = MT_init_by_array(MT_init[2], 5);
  //  unsigned long init3[5]={0x123, 0x234, 0x345, 0x456, 3};
  //  MT m3 = MT_init_by_array(init3, 5);
    MT m3 = MT_init_by_array(MT_init[3], 5);
    for (int p=0; p<n2; p++) {
      share_t r = RANDOM(m1, k);
      share_t s = RANDOM(m2, k);
      share_t t = RANDOM(m3, k);
      //r = s = t = 0; // test
      share_t u;
      if (irr_poly) {
        u = r ^ s ^ t;
      } else {
        u = (r + s + t) % k;
      }
      pa_set(R->A, p, r);
      pa_set(S->A, p, s);
      pa_set(T->A, p, t);
      for (int i=0; i<k; i++) {
        for (int j=0; j<w; j++) {
          if (irr_poly) {
            pa_set(F->A, p*k*w + i*w + j, func_table[(i^u)*w + j]); //  xor で無くても良い?
          } else {
            pa_set(F->A, p*k*w + i*w + j, func_table[((i+u)%k)*w + j]);
          }
        }
      }
    }
    MT_free(m1);
    MT_free(m2);
    MT_free(m3);
  //  printf("R "); _print(R);
  //  printf("S "); _print(S);
  //  printf("T "); _print(T);

    //_ t0 = _const(n2*k*w, 0, q);
    _ t1 = share_const_type(n*k*w, 0, q, type);
    _ t2 = share_const_type(n*k*w, 0, q, type);
    _ t3 = share_const_type(n*k*w, 0, q, type);
  //  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
    unsigned long *init0 = MT_init[0];
    MT m0 = MT_init_by_array(init0, 5);
    for (int p=0; p<n; p++) {
      for (int i=0; i<k; i++) {
        for (int j=0; j<w; j++) {
          share_t rr = RANDOM(m0, q);
          //rr = 2; // test
        //  pa_set(t1->A, p*k*w + i*w + j, rr);
        //  pa_set(t2->A, p*k*w + i*w + j, MOD(pa_get(F->A, p*k*w + i*w + j)-rr)); // 答えは加法的シェア
          share_t x = pa_get(F->A, p*k*w + i*w + j);
          if (type == SHARE_T_SHAMIR) {
            if (irr_poly) {
              pa_set(t1->A, p*k*w + i*w + j, GF_mul(1, rr, irr_poly) ^ x); // 出力は別形式でも良い
              pa_set(t2->A, p*k*w + i*w + j, GF_mul(2, rr, irr_poly) ^ x);
              pa_set(t3->A, p*k*w + i*w + j, GF_mul(3, rr, irr_poly) ^ x);
            } else {
              pa_set(t1->A, p*k*w + i*w + j, MOD(x + 1 * rr));
              pa_set(t2->A, p*k*w + i*w + j, MOD(x + 2 * rr));
              pa_set(t3->A, p*k*w + i*w + j, MOD(x + 3 * rr));
            }
          } else if (type == SHARE_T_RSS) {
            share_t ss = RANDOM(m0, q);
            //ss = 4; // test
            share_t tt;
            if (irr_poly) {
              tt = rr ^ ss;
              pa_set(t1->A, p*k*w + i*w + j, x ^ rr);
              pa_set(t2->A, p*k*w + i*w + j,     ss);
              pa_set(t3->A, p*k*w + i*w + j,     tt);
              pa_set(t1->A, p*k*w + i*w + j + n*k*w,     ss);
              pa_set(t2->A, p*k*w + i*w + j + n*k*w,     tt);
              pa_set(t3->A, p*k*w + i*w + j + n*k*w, x ^ rr);
            } else {
              tt = MOD(q*2 - rr - ss);
              pa_set(t1->A, p*k*w + i*w + j, MOD(x + rr));
              pa_set(t2->A, p*k*w + i*w + j, MOD(0 + ss));
              pa_set(t3->A, p*k*w + i*w + j, MOD(0 + tt));
              pa_set(t1->A, p*k*w + i*w + j + n*k*w, MOD(0 + ss));
              pa_set(t2->A, p*k*w + i*w + j + n*k*w, MOD(0 + tt));
              pa_set(t3->A, p*k*w + i*w + j + n*k*w, MOD(x + rr));
            }
          } else {
            printf("onehotvec_shamir3 type = %d\n", type);
          }
        }
      }
    }
    MT_free(m0);

    if (_party == 0) {
      //printf("t1 "); _print(t1);
      //printf("t2 "); _print(t2);
      //printf("t3 "); _print(t3);
      mpc_send_share_channel(TO_PARTY1, R, channel);
      mpc_send_share_channel(TO_PARTY2, S, channel);
      mpc_send_share_channel(TO_PARTY3, T, channel);
      mpc_send_share_channel(TO_PARTY1, t1, channel);
      mpc_send_share_channel(TO_PARTY2, t2, channel);      
      mpc_send_share_channel(TO_PARTY3, t3, channel);
    }
    //_free(t0);
    _free(t1);
    _free(t2);
    _free(t3);
    _free(F);
    _free(R);
    _free(S);
    _free(T);
  } else {
    R = share_const_type(n, 0, k, type);
    t = share_const_type(n*k*w, 0, q, type);
    //if (_party == 3) {
    //  mpc_recv_share_channel(FROM_PARTY3, R, channel);
    //  mpc_recv_share_channel(FROM_PARTY3, t, channel);
    //} else {
    mpc_recv_share_channel(FROM_SERVER, R, channel);
    mpc_recv_share_channel(FROM_SERVER, t, channel);
    //}
    //printf("R "); _print(R);
    //printf("t "); _print(t);

  }

// 本計算
  //_ ans = _const(n*w, 0, q);
  _ ans = share_const_type(n*w, 0, q, type);
  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      for (int j=0; j<w; j++) {
        pa_set(ans->A, p*w+j, func_table[xx*w+j]%q);
      }
    }
    free(func_table);
  } else {
    //printf("x "); _print(x);
    //printf("R "); _print(R);
    _ y = share_const_type(n2, 0, k, SHARE_T_33ADD);
    for (int p=0; p<n2; p++) {
      if (irr_poly) {
        pa_set(y->A, p, (pa_get(R->A, p) ^ pa_get(x->A, p))%k);
      } else {
      //  pa_set(y->A, p, (pa_get(R->A, p) + pa_get(x->A, p))%k); // !!!
        pa_set(y->A, p, (k - pa_get(R->A, p) + pa_get(x->A, p))%k);
      }
    }
  //  printf("y "); _print(y);
  //  _ z = _const(n, 0, k);
  //  mpc_exchange_share_channel(y, z, channel);
    _ z = shamir3_reconstruct_xor_channel(y, irr_poly, channel);
    //printf("z "); _print(z);
    if (_party == 1 || _party == 2 || _party == 3) {
      for (int p=0; p<n; p++) {
        share_t ys = pa_get(z->A, p);
        for (int j=0; j<w; j++) {
        //  pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + tt*w + j)%q);
          pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + ys*w + j)%q);
          if (type == SHARE_T_RSS) {
            pa_set(ans->A, p*w+j + n*w, pa_get(t->A, p*k*w + ys*w + j+ n*k*w)%q);
          }
        }
      }
    }
    _free(y);
    _free(z);
    _free(R);
    _free(t);
  }
  ans->type = type;
  return ans;
}
//#define onehotvec_shamir3_online_channel(x, q, irr_poly, channel) onehotvec_shamir3_type_online_channel(x, q, irr_poly, SHARE_T_SHAMIR,channel)
#define onehotvec_shamir3_shamir_online_channel(x, q, irr_poly, channel) onehotvec_shamir3_type_online_channel(x, q, irr_poly, SHARE_T_SHAMIR,channel)
#define onehotvec_shamir3_rss_online_channel(x, q, irr_poly, channel) onehotvec_shamir3_type_online_channel(x, q, irr_poly, SHARE_T_RSS,channel)


///////////////////////////////////////////////////////////////////////////
// One-hot vector
// 入力: 33ADD
// 出力: Shamir or RSS (type で指定)
///////////////////////////////////////////////////////////////////////////
_ onehotvec_shamir3_type_channel(_ x, share_t q, share_t irr_poly, int type, int channel)
{
  precomp_tables T = NULL;
  int k = blog(q-1)+1; // 出力の桁数
  if (type == SHARE_T_RSS) {
    T = PRE_OHR_tbl[k-1][channel];
  } else { // shamir
    T = PRE_OHS3_tbl[k-1][channel];
  }
  if (T != NULL) {
    return onehotvec_shamir3_type_table_channel(k, x, q, irr_poly, type, T, channel); // 長さ w の one hot vector が n 個
  } else {
    if (_opt.warn_precomp) {
      printf("onehotvec_shamir3_type_online_channel k=%d irr_poly=%x\n", k, irr_poly);
    }
    return onehotvec_shamir3_type_online_channel(x, q, irr_poly, type, channel);
  }
}
#define onehotvec_shamir3(x, q, irr_poly) onehotvec_shamir3_type_channel(x, q, irr_poly, SHARE_T_SHAMIR, 0)

_pair RndOhv_rss(int n, int d, int channel);
_ Ohv(_ v, _pair rndohv);

_bits tablelookup_3party(_s3 x, share_t *tbl, share_t q, share_t irr_poly, int type)
{
  int n = len(x);
  int k = blog(q-1)+1; // 出力の桁数
  share_t w = order(x);

  int n2 = n;
  if (type == SHARE_T_RSS) n2 = n*2;

  _bits ans = share_const_bits_3party(n2, 0, q, k);
  for (int d=0; d<ans->d; d++) ans->a[d]->type = type;

//  _s ohv = onehotvec_shamir3_table(k, x, q, irr_poly, PRE_OHS3_tbl[k-1][0]); // 長さ w の one hot vector が n 個
//  _s ohv = onehotvec_shamir3_online_channel(x, q, irr_poly, 0);
#if 0
  _s ohv2 = onehotvec_shamir3_type_channel(x, q, irr_poly, type, 0); // 長さ w の one hot vector が n 個
#endif
  _pair rndohv = RndOhv_rss(n, 4, 0);
  _s ohv = Ohv(x, rndohv);
  //printf("ohv "); _print(ohv);
  //printf("ohv "); _print_debug_rss(ohv, 1);
  //printf("ohv2 "); _print(ohv2);
  //printf("ohv2 "); _print_debug_rss(ohv2, 1);

  for (int i=0; i<n2; i++) {
    for (int j=0; j<k; j++) { // 出力の桁ごとに計算
    //  printf("j %d\n", j);
      _ V = ans->a[j];
      for (share_t x=0; x<w; x++) {
        share_t y = tbl[x]; // 出力が y と想定して計算
        if (y & (1<<j)) { // 出力の j ビット目が 1 なら
          share_t tmp = pa_get(V->A, i);
          tmp ^= pa_get(ohv->A, i*w+x);
          pa_set(V->A, i, tmp);
        }
      }
    }    
  }
  _free(ohv);
  _free(rndohv.x); _free(rndohv.y);
  return ans;
}


#endif