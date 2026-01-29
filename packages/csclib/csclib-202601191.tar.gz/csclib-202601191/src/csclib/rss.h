#ifndef _RSS_H
 #define _RSS_H

#include <stdlib.h>
//#include "share.h"

/****************************************************************************
 * 複製秘密分散 (Replicated Secret Sharing)
 * 配列長は2倍になる
 ****************************************************************************/

int len_rss(_ a)
{
  if (a->type != SHARE_T_RSS) {
    printf("len_rss: type = %d\n", a->type);
  }
  return a->n / 2;
}


share_array share_rss_GF_new(int n, share_t q, share_t *A, share_t irr_poly)
{
  int i;
  NEWT(share_array, ans);
  int k;

  ans->type = SHARE_T_RSS;
  ans->irr_poly = irr_poly;
  ans->n = n*2; // 複製する

  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;

  ans->A = pa_new(n*2, k);

  if (_party < 0) {
    for (i=0; i<n; i++) {
      pa_set(ans->A, i, A[i]);
      pa_set(ans->A, i+n, 0);
    }
    return ans;
  }

  if (_party == 0) {
    packed_array A1, A2, A3;
    A1 = pa_new(n*2, k);
    A2 = pa_new(n*2, k);
    A3 = pa_new(n*2, k);
    for (i=0; i<n; i++) {
      share_t r1, r2, r3;
      pa_set(ans->A, i, A[i]);
      pa_set(ans->A, i+n, 0);
      r1 = RANDOM0(q);
      r2 = RANDOM0(q);
      if (irr_poly) {
        r3 = r1 ^ r2;
        pa_set(A1, i, A[i] ^ r1);
        pa_set(A2, i, 0    ^ r2);
        pa_set(A3, i, 0    ^ r3);
        pa_set(A1, i+n, 0  ^ r2);
        pa_set(A2, i+n, 0  ^ r3);
        pa_set(A3, i+n, A[i] ^ r1);
      } else {
        r3 = MOD(q*2 - r1 - r2);
        pa_set(A1, i, MOD(A[i] + r1));
        pa_set(A2, i, MOD(0    + r2));
        pa_set(A3, i, MOD(0    + r3));
        pa_set(A1, i+n, MOD(0  + r2));
        pa_set(A2, i+n, MOD(0  + r3));
        pa_set(A3, i+n, MOD(A[i] + r1));
      }
    }
    if (_party == 0) {
      mpc_send_pa(TO_PARTY1, A1);  //send_7 += pa_size(A1);
      mpc_send_pa(TO_PARTY2, A2);
      mpc_send_pa(TO_PARTY3, A3);
    }

    pa_free(A1);
    pa_free(A2);
    pa_free(A3);
  } else {
    //mpc_recv_share(FROM_SERVER, ans);
    mpc_recv_pa(FROM_SERVER, ans->A);
  }

  return ans;
}
#define share_rss_new(n, q, A) share_rss_GF_new(n, q, A, 0)
#define rss_new share_rss_new

_ share_const_rss_GF(int n, share_t v, share_t q, share_t irr_poly)
{
  _ ans = share_const_type(n, 0, q, SHARE_T_RSS);
  ans->type = SHARE_T_RSS;
  ans->irr_poly = irr_poly;

  if (_party <= 1) {
    pa_iter itr = pa_iter_new(ans->A);
    for (int i=0; i<n; i++) {
      //pa_set(ans->A, i, v);
      pa_iter_set(itr, v);
    }
    pa_iter_flush(itr);
  }
  if (_party == 3) {
    //pa_iter itr = pa_iter_pos_new(ans->A, n);
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i+n, v);
      //pa_iter_set(itr, v);
    }
    //pa_iter_flush(itr);
  }
  return ans;
}
#define share_const_rss(n, v, q) share_const_rss_GF(n, v, q, 0)
#define _const_rss share_const_rss



/***********************************************************************
 * irr_poly を指定する必要があるか．
***********************************************************************/
_ share_rss_reconstruct(_ x, share_t irr_poly)
{
  if (x->type != SHARE_T_RSS) {
    printf("share_rss_reconstruct: type = %d\n", x->type);
  }

//  int n = len(x) / 2;
  int n = x->n / 2;

  if (_party <= 0) {
    _ ans = _slice_raw(x, 0, n); 
    ans->type = SHARE_T_RAW;
    return ans;
  }

  _ ans, tmp1, tmp2;
  share_t q = order(x);
  if (_party == 1) {
    tmp1 = _slice_raw(x, 0, n); // x1
    //printf("x "); _print(x);
    //printf("send to party 2 "); _print(tmp1);
    mpc_send_share(TO_PARTY2, tmp1);
  }
  if (_party == 2) {
    tmp1 = _slice_raw(x, 0, n); // x2
    //printf("x "); _print(x);
    //printf("send to party 3 "); _print(tmp1);
    mpc_send_share(TO_PARTY3, tmp1);
  }
  if (_party == 3) {
    tmp1 = _slice_raw(x, 0, n); // x3
    //printf("x "); _print(x);
    //printf("send to party 1 "); _print(tmp1);
    mpc_send_share(TO_PARTY1, tmp1);
  }
  if (_party == 1) {
    tmp2 = share_const_type(n, 0, q, SHARE_T_33ADD);
    mpc_recv_share(FROM_PARTY3, tmp2);
  }
  if (_party == 2) {
    tmp2 = share_const_type(n, 0, q, SHARE_T_33ADD);
    mpc_recv_share(FROM_PARTY1, tmp2);
  }
  if (_party == 3) {
    tmp2 = share_const_type(n, 0, q, SHARE_T_33ADD);
    mpc_recv_share(FROM_PARTY2, tmp2);
  }

  ans = share_const_type(n, 0, q, SHARE_T_33ADD);
  for (int i=0; i<n; i++) {
    share_t z, x1, x2, x3;
    x1 = pa_get(x->A, i);
    x2 = pa_get(x->A, i+n);
    x3 = pa_get(tmp2->A, i);
    if (irr_poly) {
      z = x1 ^ x2 ^ x3;
    } else {
      z = MOD(x1 + x2 + x3);
    }
    pa_set(ans->A, i, z);
  }

  ans->type = SHARE_T_RAW;
  ans->irr_poly = irr_poly;
  return ans;
}
#define rss_reconstruct(x, xor) share_rss_reconstruct(x, xor)


_ vadd_rss(_ a, _ b)
{
  if (a->type != SHARE_T_RSS || b->type != SHARE_T_RSS) {
    printf("vadd_rss: type = %d, %d\n", a->type, b->type);
  }
  if (_party > 3) return NULL; // 要check
  return vadd(a, b);
}
#define _vadd_rss vadd_rss

_ vsub_rss(_ a, _ b)
{
  if (a->type != SHARE_T_RSS || b->type != SHARE_T_RSS) {
    printf("vsub_rss: type = %d, %d\n", a->type, b->type);
  }
  if (_party > 3) return NULL; // 要check
  return vsub(a, b);
}
#define _vsub_rss vsub_rss


_ vadd_rss_GF(_ a, _ b)
{
//  if (_party > 3) return NULL;
  if (_party > max_partyid(a)) return NULL;
//  int n = len(a);
  int n = a->n;
  share_t q = order(a);
  if (b->n != n || order(b) != q) {
    printf("vadd_rss_GF: len %d %d order %d %d\n", n, b->n, q, order(b));
    exit(1);
  }
#if 0
  _ ans = _const(n, 0, q);
  for (int i=0; i<n; i++) {
    share_t c;
    c = pa_get(a->A, i) ^ pa_get(b->A, i);
    pa_set(ans->A, i, c);
  }
#else
  _ ans = vadd_GF(a, b);
#endif
  ans->type = a->type;
  return ans;
}


_ smul_rss(share_t s, _ a) // s は公開値
{
  if (a->type != SHARE_T_RSS) {
    printf("smul_rss: type = %d\n", a->type);
  }
  if (_party >  3) return NULL; // 要check
  return smul(s, a);
}
#define _smul_rss smul_rss

_ smul_rss_GF(share_t s, _ a, share_t irr_poly)
{
  if (a->type != SHARE_T_RSS) {
    printf("smul_rss_GF: type = %d\n", a->type);
  }
  if (_party >  3) return NULL;
  int n = len(a);
  share_t q = order(a);
  _ ans = _const(2*n, 0, q);
  NEWITER(itr_ans, ans);
  NEWITER(itr_a, a);
  for (int i=0; i<2*n; i++) {
    share_t c;
    c = GF_mul(s, pa_iter_get(itr_a), irr_poly);
    pa_iter_set(itr_ans, c);
  }
  pa_iter_flush(itr_ans);
  pa_iter_free(itr_a);
  ans->type = SHARE_T_RSS;
  ans->irr_poly = irr_poly;
  return ans;
}

_ slice_rss(_ a, int start, int end)
{
  if (a->type != SHARE_T_RSS) {
    printf("slice_rss: type = %d\n", a->type);
  }
  if (_party >  3) return NULL; // 要check
  int n = len_rss(a);
  int len = end - start;

  _ ans = _const_rss(len, 0, a->q);
  for (int i=0; i<len; i++) {
    pa_set(ans->A, i, pa_get(a->A, start+i));
    pa_set(ans->A, i+len, pa_get(a->A, start+i+n));
  }
  ans->irr_poly = a->irr_poly;
  return ans;
}

_s3 vmul_rss(_ a, _ b)
{
//  if (a->irr_poly != irr_poly || b->irr_poly != irr_poly) {
//    printf("vmul_rss_GF: a->irr_poly = %x b->irr_poly = %x irr_poly = %x\n", a->irr_poly, b->irr_poly, irr_poly);
//  }

  if (a->type != SHARE_T_RSS || b->type != SHARE_T_RSS) {
    printf("vmul_rss: type = %d, %d\n", a->type, b->type);
  }
  if (_party > max_partyid(a)) return NULL; // 要check

  int n = len_rss(a);
  if (n != len_rss(b)) {
    printf("vmul_rss_GF: len(a) = %d len(b) = %d\n", n, len_rss(b));
    exit(1);
  }
  share_t irr_poly = a->irr_poly;
  if (_party <= 0) {
    _ a2 = _slice_raw(a, 0, n);
    _ b2 = _slice_raw(b, 0, n);
    _ ans = _dup(a2);
    ans->type = SHARE_T_33ADD;
    if (irr_poly) {
      //ans = vmul_GF(a2, b2, irr_poly);
      for (int i=0; i<n; i++) {
        pa_set(ans->A, i, GF_mul(pa_get(a->A,i), pa_get(b->A,i), irr_poly));
      }
    } else {
      //ans = vmul(a2, b2);
      share_t q = order(a);
      for (int i=0; i<n; i++) {
        pa_set(ans->A, i, LMUL(pa_get(a->A,i), pa_get(b->A,i), q));
      }
    }
    ans->type = SHARE_T_33ADD;
    _free(a2);
    _free(b2);
    return ans;
  }
  _ ans = share_const_type(n, 0, order(a), SHARE_T_33ADD);
  //ans->type = SHARE_T_33ADD;
  share_t q = order(a);
  if (q != order(b)) {
    printf("vmul_rss: order = %d, %d\n", q, order(b));
  }
  for (int i=0; i<n; i++) {
    share_t a1 = pa_get(a->A, i);
    share_t a2 = pa_get(a->A, i+n);
    share_t b1 = pa_get(b->A, i);
    share_t b2 = pa_get(b->A, i+n);
    share_t z;
    if (irr_poly) {
      z = GF_mul(a1, b1, irr_poly);
      z = GFADD(z, GF_mul(a1, b2, irr_poly), irr_poly);
      z = GFADD(z, GF_mul(a2, b1, irr_poly), irr_poly);
    } else {
      z = MOD(a1*b1 + a1*b2 + a2*b1);
    }
    pa_set(ans->A, i, z);
  }
  return ans;
}
//#define vmul_rss(a, b) vmul_rss_GF(a, b, 0)
#define _vadd_rss vadd_rss

///////////////////////////////////////////////////////////////////////////
// 33 Additive から複製秘密分散 (RSS) のシェアを作る
///////////////////////////////////////////////////////////////////////////
_ shamir3_to_rss_GF_channel(_ x, share_t irr_poly, int channel)
{
  if (x->type != SHARE_T_33ADD) {
    printf("shamir3_to_rss: type = %d\n", x->type);
  }

  _ ans;
  int n = len(x);
  share_t q = order(x);
  ans = share_const_type(n, 0, q, SHARE_T_RSS);
  ans->type = SHARE_T_RSS;
  ans->irr_poly = irr_poly;
  if (_party <= 0) {
    NEWITER(itr_ans, ans);
    NEWITER(itr_x, x);
    for (int i=0; i<n; i++) {
      pa_iter_set(itr_ans, pa_iter_get(itr_x));
      //pa_set(ans->A, i+n, 0); // 既に 0 になっている
    }
    pa_iter_flush(itr_ans);
    pa_iter_free(itr_x);

    return ans;
  }

  if (_party == 1) {
    NEWITER(itr_ans, ans);
    NEWITER(itr_x, x);
    for (int i=0; i<n; i++) {
      share_t r = RANDOM(mt_[TO_PARTY2][channel], q);
      //r = 0; //test
      share_t z;
      if (irr_poly) {
        z = pa_iter_get(itr_x) ^ r;
      } else {
        z = MOD(pa_iter_get(itr_x) + r);
      }
      pa_iter_set(itr_ans, z);
    }
    pa_iter_flush(itr_ans);
    pa_iter_free(itr_x);
    _ tmp = _slice_raw(ans, 0, n);
    //printf("send to party 3 "); _print(tmp);
    mpc_send_share_channel(TO_PARTY3, tmp, channel);
    mpc_recv_share_channel(FROM_PARTY2, tmp, channel);
    //printf("recv from party 2 "); _print(tmp);
    NEWITER(itr_tmp, tmp);
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i+n, pa_get(tmp->A, i));
      //pa_iter_set(itr_ans, pa_iter_get(itr_tmp));
    }
    pa_iter_free(itr_tmp);
    //pa_iter_flush(itr_ans);
    _free(tmp);
  }
  if (_party == 3) {
    NEWITER(itr_ans, ans);
    NEWITER(itr_x, x);
    for (int i=0; i<n; i++) {
      share_t s = RANDOM(mt_[TO_PARTY2][channel], q);
      //s = 0; //test
      share_t z;
      if (irr_poly) {
        z = pa_iter_get(itr_x) ^ s;
      } else {
        z = MOD(pa_iter_get(itr_x) + s);
      }
      //pa_set(ans->A, i, MOD(pa_get(x->A, i) + s));
      pa_iter_set(itr_ans, z);
    }
    pa_iter_flush(itr_ans);
    pa_iter_free(itr_x);
    _ tmp = _slice_raw(ans, 0, n);
    //printf("send to party 2 "); _print(tmp);
    mpc_send_share_channel(TO_PARTY2, tmp, channel);
    mpc_recv_share_channel(FROM_PARTY1, tmp, channel);
    //printf("recv from party 1 "); _print(tmp);
    NEWITER(itr_tmp, tmp);
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i+n, pa_get(tmp->A, i));
      //pa_iter_set(itr_ans, pa_iter_get(itr_tmp));
    }
    //pa_iter_flush(itr_ans);
    pa_iter_free(itr_tmp);
    _free(tmp);
  }
  if (_party == 2) {
    NEWITER(itr_ans, ans);
    NEWITER(itr_x, x);
    for (int i=0; i<n; i++) {
      share_t r = RANDOM(mt_[TO_PARTY1][channel], q);
      share_t s = RANDOM(mt_[TO_PARTY3][channel], q);
      //r = 0; //test
      //s = 0; //test
      share_t z;
      if (irr_poly) {
        z = pa_iter_get(itr_x) ^ r ^ s;
      } else {
        z = MOD(pa_iter_get(itr_x) - r - s);
      }
      pa_set(ans->A, i, z);
      //pa_iter_set(itr_ans, z);
    }
    //pa_iter_flush(itr_ans);
    pa_iter_free(itr_x);
    _ tmp = _slice_raw(ans, 0, n);
    //printf("send to party 1 "); _print(tmp);
    mpc_send_share_channel(TO_PARTY1, tmp, channel);
    mpc_recv_share_channel(FROM_PARTY3, tmp, channel);
    //printf("recv from party 3 "); _print(tmp);
    NEWITER(itr_tmp, tmp);
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i+n, pa_get(tmp->A, i));
      //pa_iter_set(itr_ans, pa_iter_get(itr_tmp));
    }
    pa_iter_free(itr_tmp);
    //pa_iter_flush(itr_ans);
    _free(tmp);
  }

  return ans;

}
#define shamir3_to_rss(x) shamir3_to_rss_GF_channel(x, 0, 0)


void _print_debug_rss(_s x, int xor)
{
  _ tmp = share_rss_reconstruct(x, xor);
  _print(tmp);
  _free(tmp);
}

void share_check_rss(share_array a, share_t irr_poly)
{
//  if (_party >  2) return; // 要検討
  if (a->type != SHARE_T_RSS || irr_poly > 0) {
    printf("share_check_rss: type = %d irr_poly = %x\n", a->type, irr_poly);
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
    mpc_recv_pa(FROM_PARTY2, A3);
    if (_party == 0) {
      for (i=0; i<n; i++) {
        share_t x, r1, r2;
        r1 = MOD(pa_get(A2, i) - pa_get(A1, i)); 
        r2 = MOD(pa_get(A3, i) - pa_get(A2, i)); 
        x = MOD(pa_get(A1, i) - r1);
        if ((u64)x != pa_get(a->A, i)) {
          printf("i = %d A = %d %d A1 = %d A2 = %d A3 = %d\n", i, (int)pa_get(a->A, i), (int)x, (int)pa_get(A1,i), (int)pa_get(A2,i), (int)pa_get(A3,i));
          err=1;
          exit(1);
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
#define _check_rss share_check_rss

share_array share_rss_random_channel(int n, share_t q, share_t m, int channel)
{
  int i;
  NEWT(share_array, ans);
  int k;

  ans->type = SHARE_T_RSS;
  ans->irr_poly = 0;
  ans->n = n*2; // 複製する

  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;

  ans->A = pa_new(n*2, k);

  if (_party <= 0) {
    for (i=0; i<n; i++) {
      pa_set(ans->A, i, RANDOM0(m));
      pa_set(ans->A, i+n, 0);
    }
    return ans;
  }

  int next_id = (_party % 3)+1;
  int prev_id = _party - 1;  if (prev_id == 0) prev_id = 3;
  NEWITER(itr_ans, ans);
  for (i=0; i<n; i++) {
    share_t r = RANDOM(mt_[prev_id][channel], m);
    pa_iter_set(itr_ans, r);
  }
  for (i=0; i<n; i++) {
    share_t r = RANDOM(mt_[next_id][channel], m);
    pa_iter_set(itr_ans, r);
  }
  pa_iter_flush(itr_ans);

  return ans;
}
#define share_rss_random(n, q) share_rss_random_channel(n, q, 0)

_pair RndOhv_rss(int n, int d, int channel)
{
  int m = 1<<d; // one hot vector の長さ
  //m = 16;

  _ r[16];
  _ tmp;

  share_t q = 2;
  r[0] = share_const_rss(n, 1, m); // true
  r[1] = share_rss_random_channel(n, m, q, channel); // r0
  r[2] = share_rss_random_channel(n, m, q, channel); // r1
  r[4] = share_rss_random_channel(n, m, q, channel); // r2
  r[8] = share_rss_random_channel(n, m, q, channel); // r3
  r[0]->irr_poly = r[1]->irr_poly = r[2]->irr_poly = r[4]->irr_poly = r[8]->irr_poly = q;
  //printf("r[%d] ", 1); _print(r[1]);
  tmp = vmul_rss(r[2], r[1]);      // r10
  //printf("tmp "); _print(tmp); _print_debug_shamir3(tmp, 1);
  r[2+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  //printf("r[%d] ", 3); _print(r[3]);
  tmp = vmul_rss(r[4], r[1]);      // r20
  r[4+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[4], r[2]);      // r21
  r[4+2] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[1]);      // r30
  r[8+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[2]);      // r31
  r[8+2] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[4]);      // r32
  r[8+4] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[4], r[2+1]);  // r210
  r[4+2+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[2+1]);  // r310
  r[8+2+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[4+1]);  // r320
  r[8+4+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8], r[4+2]);  // r321
  r[8+4+2] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);
  tmp = vmul_rss(r[8+4], r[2+1]); // r3210
  r[8+4+2+1] = shamir3_to_rss_GF_channel(tmp, q, channel); _free(tmp);

  //for (int i=0; i<m; i++) {
  //  printf("r[%d] ", i); _print(r[i]);
  //}


#if 0
  int m = 1<<d; // one hot vector の長さ
  for (int j=0; j<m; j++) {
    printf("j %d\n", j);
    for (int k=0; k<m; k++) { // 多項式を展開した項それぞれで
      int idx = 0;
      for (int i=0; i<d; i++) {
        if (k & (1<<i)) { // r_i を選択
          if (idx >= 0) idx += 1<<i;
        } else {
          if (j & (1<<i)) {
            idx = -1;
          }
        }
      }
      if (idx >= 0) printf("k %d idx %d\n", k, idx);
    }
  }    
#endif
  _ ohv = share_const_rss(n*m, 0, m);

  //for (int p=0; p<n; p++) {
    for (int j=0; j<m; j++) {
      _ tmp = share_const_type(n, 0, m, SHARE_T_RSS);
      tmp->irr_poly = q;
      for (int k=0; k<m; k++) { // 多項式を展開した項それぞれで
        int idx = 0;
        for (int i=0; i<d; i++) {
          if (k & (1<<i)) { // r_i を選択
            if (idx >= 0) idx += 1<<i;
          } else {
            if (j & (1<<i)) {
              idx = -1;
            }
          }
        }
        if (idx >= 0) {
          vadd_(tmp, r[idx]);
          //printf("j=%d k=%d idx=%d ", j, k, idx);
          //_print(r[idx]);
          //printf("tmp "); _print(tmp);
        }
      }
      //share_setshares(ohv, j*n, (j+1)*n, tmp, 0);
#if 0
      for (int p=0; p<n*2; p++) {
        //_setshare(ohv, p*m+j, tmp, p);
        share_setraw(ohv, p*m+j, share_getraw(tmp, p));
      }
#else
      for (int p=0; p<n; p++) {
        share_setraw(ohv, p*m+j, share_getraw(tmp, p));
        share_setraw(ohv, p*m+j+m*n, share_getraw(tmp, p+n));
      }
#endif
      _free(tmp);
    }
  //}

  _ s[4];
  s[0] = share_rss_random_channel(n, m, q, channel);
  s[1] = share_rss_random_channel(n, m, q, channel);
  s[2] = share_rss_random_channel(n, m, q, channel);
  s[3] = share_rss_random_channel(n, m, q, channel);
  s[0]->irr_poly = s[1]->irr_poly = s[2]->irr_poly = s[3]->irr_poly = q;

  _ rr[4];
  for (int k=0; k<d; k++) {
    rr[k] = _slice_raw(r[1<<k], 0, n);
    if (_party > 0) {
      _ s1 = _slice_raw(s[k], 0, n);
      _ s2 = _slice_raw(s[k], n, n*2);
      vadd_(rr[k], s1);
      vadd_(rr[k], s2);
      _free(s1); _free(s2);
    }
  }
#if 0
  _ E = share_const_type(n*4, 0, 2, SHARE_T_33ADD);
  for (int p=0; p<n; p++) {
    for (int k=0; k<d; k++) {
      share_setshare(E, p*4+k, rr[k], p);
    }
  }
#else
  _ E = share_const_type(n, 0, m, SHARE_T_33ADD);
  for (int p=0; p<n; p++) {
    share_t x = 0;
    for (int k=0; k<d; k++) {
      x ^= (1<<k) * (share_getraw(rr[k], p));
    }
    share_setraw(E, p, x);
  }
#endif
  //printf("E "); _print(E);
  //printf("ohv "); _print(ohv);

  for (int i=0; i<m; i++) {
    _free(r[i]);
  }
  for (int i=0; i<d; i++) {
    _free(rr[i]);
    _free(s[i]);
  }

  _pair ans = {E, ohv};
  return ans;
}

_ Ohv(_ v, _pair rndohv)
{
  int n = len(v);
  int m = order(v);
  _ r = rndohv.x;
  _ e = rndohv.y;
  //printf("r "); _print(r); _print_debug_shamir3(r, 1);
  //printf("e "); _print(e); _print_debug_rss(e, 1);
  _ w = vadd_GF(v, r);
  _ wr = shamir3_reconstruct_xor(w, 1);
  //printf("wr "); _print(wr);
  _ z = _dup(e);
  for (int i=0; i<n; i++) {
    int idx = share_getraw(wr, i);
    for (int j=0; j<m; j++) {
      int x = j ^ idx;
      _setshare(z, i*m + j, e, i*m + x);      
      _setshare(z, n*m + i*m + j, e, n*m + i*m + x);      
    }
  }
  _free(w);
  _free(wr);
  return z;
  //printf("z "); _print(z); _print_debug_rss(z, 1);
}

#endif
