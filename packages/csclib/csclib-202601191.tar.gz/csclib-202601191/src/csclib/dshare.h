#ifndef _DSHARE_H
 #define _DSHARE_H
//#include "share.h"
#include "func.h"
#include "compare.h"
#include "bits_tools.h"

extern long total_perm;

//extern long send_1, send_2, send_3, send_4, send_5;


/////////////////////////////////////////////////
// 置換 (平文) 0, 1, ..., n-1
/////////////////////////////////////////////////
typedef packed_array perm;

typedef struct dshare {
// public
  int n;
  share_t q;       // 配列の要素の位数
  int bs;

// P0 piはn要素の置換
  perm pi;
  perm p1, p2p; // pi = p1・p2p
  perm p2, p1p; // pi = p2・p1p

// P1, P2
  perm g, gp; // P1:(g, gp) = (p1, p1p)   P2:(g, gp) = (p2, p2p)


/////////////////
// correlated_random
/////////////////

// P0   a1,b1,a2,b2,cはそれぞれそれぞれn*bs次元ベクトル
  perm a1, b1;  // b1 = a2・p1p + c
  perm a2, b2;  // b2 = a1・p2p - c

// P1, P2
  perm a, b;  // P1:(a, b) = (a1, b1)   P2:(a, b) = (a2, b2)

}* dshare;

static perm perm_id(int n)
{
  if (_party >  2) return NULL;
  perm pi;
  int i;
  int k = blog(n-1)+1;
  pi = pa_new(n, k);

#if 0
  for (i=0; i<n; i++) pa_set(pi, i, i);
#else
  pa_iter itr = pa_iter_new(pi);
  for (i=0; i<n; i++) pa_iter_set(itr, i);
  pa_iter_flush(itr);
#endif

  return pi;
}

static void perm_print(int n, perm pi)
{
  if (_party >  2) return;
  int i;
  printf("(");
  for (i=0; i<n; i++) {
    printf("%d", (int)pa_get(pi, i));
    if (i < n-1) printf(" ");
  }
  printf(")\n");
}

static void perm_free(perm pi)
{
  if (_party >  2);
  pa_free(pi);
}


static perm perm_inverse_old(perm pi)
{
  if (_party >  2) return NULL;
  perm pi_inv;
  pi_inv = perm_id(pi->n);

  int n = pi->n;
  for (int i=0; i<n; i++) {
#if 0
    if ((pa_get(pi, i) < 0) || (pa_get(pi, i) >= (u64)n)) {
      printf("pi[%d] = %d", i, (int)pa_get(pi, i));
      exit(1);
    }
#endif
    //pa_set(pi_inv, pa_get(pi, i) % n, i);
    share_t x = pa_get(pi, i);
    if ((x < 0) || (x >= (u64)n)) {
      printf("pi[%d] = %d", i, (int)x);
      exit(1);
    }
    pa_set(pi_inv, x % n, i);
  }
  return pi_inv;
}

static perm perm_inverse(perm pi)
{
  if (_party >  2) return NULL;
  perm pi_inv;
  //pi_inv = perm_id(pi->n);
  share_t *pi_inv_tmp;
  NEWA(pi_inv_tmp, share_t, pi->n);

  pa_iter itr = pa_iter_new(pi);

  int n = pi->n;
  for (int i=0; i<n; i++) {
#if 0
    if ((pa_get(pi, i) < 0) || (pa_get(pi, i) >= (u64)n)) {
      printf("pi[%d] = %d", i, (int)pa_get(pi, i));
      exit(1);
    }
#endif
    //pa_set(pi_inv, pa_get(pi, i) % n, i);
    share_t x = pa_iter_get(itr);
    //if (x != pa_get(pi, i)) {
    //  printf("x %d get %d\n", x, pa_get(pi, i));
    //}
    //printf("pi[%d] = %d", i, (int)x);
    if ((x < 0) || (x >= (u64)n)) {
      printf("pi[%d] = %d", i, (int)x);
      exit(1);
    }
    //pi_inv_tmp[x % n] = i;
    pi_inv_tmp[x] = i;
    //pa_set(pi_inv, x % n, i);
  }
  pi_inv = pa_pack(n, blog(n-1)+1, pi_inv_tmp);
#if 0
  for (int i=0; i<n; i++) {
    if (pi_inv_tmp[i] != pa_get(pi_inv2, i)) {
      printf("%d %d %d\n", i, pi_inv_tmp[i], pa_get(pi_inv2, i));
    }
  }
#endif
  pa_iter_free(itr);
  free(pi_inv_tmp);
  return pi_inv;
}

//////////////////////////////////////////////////////////////////////
// ランダムな置換 (平文)
//////////////////////////////////////////////////////////////////////
static perm perm_random0(MT mt, int n)
{
  if (_party >  2) return NULL;
  perm pi = perm_id(n);
  perm pi2 = perm_id(n);
  int i, j, m;
//  share_t v1, v2;

  for (m=0; m<n; m++) {
  //  i = RANDOM0(n-m);
    i = RANDOM(mt, n-m);
    j = pa_get(pi2, i);
    pa_set(pi, j, m);
    pa_set(pi2, i, pa_get(pi2, n-1-m));
  }
  pa_free(pi2);
//  printf("perm_random: ");  perm_print(n, pi);
  return pi;
}

static perm perm_random(MT mt, int n)
{
  if (_party >  2) return NULL;
  //perm pi = perm_id(n);
  //perm pi2 = perm_id(n);
  int i, j, m;
//  share_t v1, v2;
  share_t *pi_tmp, *pi2_tmp;
  NEWA(pi_tmp, share_t, n);
  NEWA(pi2_tmp, share_t, n);
  for (int i=0; i<n; i++) pi2_tmp[i] = i;
  for (m=0; m<n; m++) {
  //  i = RANDOM0(n-m);
    i = RANDOM(mt, n-m);
    //j = pa_get(pi2, i);
    j = pi2_tmp[i];
    //pa_set(pi, j, m);
    pi_tmp[j] = m;
    //pa_set(pi2, i, pa_get(pi2, n-1-m));
    pi2_tmp[i] = pi2_tmp[n-1-m];
  }
  //pa_free(pi2);
//  printf("perm_random: ");  perm_print(n, pi);
  perm pi = pa_pack(n, blog(n-1)+1, pi_tmp);
  free(pi_tmp); free(pi2_tmp);
  return pi;
}

static _ share_random_perm(int n)
{
  if (_party >  2) return NULL;
  int k = blog(n-1)+1;
  _ ans = share_const(n, 0, 1<<k);
  if (_party <= 0) {
    perm p = perm_random(mt0, n); // channel?
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i, pa_get(p, i));
    }
    perm_free(p);
  }
  return ans;
}
#define _random_perm share_random_perm


/////////////////////////////////////////////////////
// 置換 q に対し p・q を計算
/////////////////////////////////////////////////////
static perm block_perm_apply(int bs, perm p, perm q) {
  if (_party >  2) return NULL;
  perm pq;
  int k = p->w;
  int n = q->n;
  pq = pa_new(n*bs, k);
  pa_iter itr_pq = pa_iter_new(pq);
  pa_iter itr_q = pa_iter_new(q);
  share_t *p_raw = pa_unpack(p);
  for (int i = 0; i < n; ++i) {
    share_t vq = pa_iter_get(itr_q);
    for (int j = 0; j < bs; ++j) {
      //pa_set(pq, i*bs + j, pa_get(p, pa_get(q, i)*bs + j));
      //pa_set(pq, i*bs + j, pa_get(p, vq*bs + j));
      //pa_iter_set(itr_pq, pa_get(p, vq*bs + j));
      pa_iter_set(itr_pq, p_raw[vq*bs + j]);
    }
  }
  pa_iter_flush(itr_pq);  pa_iter_free(itr_q);
  free(p_raw);
  return pq;
}
#define perm_apply(p, q) block_perm_apply(1, p, q)

static share_array block_share_perm(int bs, _ x, perm pi) {
  if (_party >  2) return NULL;
  if (x->n/bs != pi->n) {
    printf("block_share_perm: x->n %d pi->n %ld\n", x->n, pi->n);
  }
  _ ans = _dup(x);
  int n = len(x)/bs;
  pa_iter itr_ans = pa_iter_new(ans->A);
  //pa_iter_new(ans->A);
  pa_iter itr_pi = pa_iter_new(pi);
  share_t *x_raw = pa_unpack(x->A);
  for (int i = 0; i < n; ++i) {
    share_t v = pa_iter_get(itr_pi);
    //printf("v %d\n", v);
    for (int j = 0; j < bs; ++j) {
    //  _setshare(ans, i*bs + j, x, pa_get(pi, i) * bs + j);
    //  share_t v = pa_iter_get(pi);
      //printf("x_raw[%d] = %d\n", v*bs+j, x_raw[v *bs + j]);
      pa_iter_set(itr_ans, x_raw[v *bs + j]);
    }
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_pi);
  free(x_raw);
  //pa_iter_new(ans->A);
  return ans;
}
#define share_perm(a, pi) block_share_perm(1, a, pi) 



/////////////////////////////////////////////////////////////////////////////
// dshare の相関乱数をオンラインで計算する
/////////////////////////////////////////////////////////////////////////////
static void block_dshare_correlated_random_channel(dshare ds, int channel) {
  if (_party >  2) return;
    int bs = ds->bs;
    int n = ds->n;
    share_t q = ds->q;
    int k = blog(q - 1) + 1;
    if (_party <= 0) {
        ds->a1 = pa_new(n*bs, k);
        ds->a2 = pa_new(n*bs, k);
        perm c = pa_new(n*bs, k);

        pa_iter itr_a1 = pa_iter_new(ds->a1);
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            //pa_set(ds->a1, i*bs+j, RANDOM(mt_[TO_PARTY1][channel], q));
            pa_iter_set(itr_a1, RANDOM(mt_[TO_PARTY1][channel], q));
          }
        }
        pa_iter_flush(itr_a1);
      //  printf("a1 "); perm_print(n*bs, ds->a1);
        pa_iter itr_a2 = pa_iter_new(ds->a2);
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            //pa_set(ds->a2, i*bs+j, RANDOM(mt_[TO_PARTY2][channel], q));
            pa_iter_set(itr_a2, RANDOM(mt_[TO_PARTY2][channel], q));
          }
        }
        pa_iter_flush(itr_a2);
      //  printf("a2 "); perm_print(n*bs, ds->a2);
        pa_iter itr_c = pa_iter_new(c);
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            //pa_set(c, i*bs+j, RANDOM(mt0, q));
            //pa_iter_set(itr_c, RANDOM(mt0, q));
            pa_iter_set(itr_c, RANDOM(mt_[0][channel], q));
          //  pa_set(c, i*bs+j, 0);
          }
        }
        pa_iter_flush(itr_c);
        ds->b1 = block_perm_apply(bs, ds->a2, ds->p1p);
        ds->b2 = block_perm_apply(bs, ds->a1, ds->p2p);
      //  printf("b1 "); perm_print(n*bs, ds->b1);
      //  printf("b2 "); perm_print(n*bs, ds->b2);

        pa_iter itr_b1r = pa_iter_new(ds->b1);
        pa_iter itr_b2r = pa_iter_new(ds->b2);
        pa_iter itr_b1w = pa_iter_new(ds->b1);
        pa_iter itr_b2w = pa_iter_new(ds->b2);
        itr_c = pa_iter_new(c);
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            //int p = i*bs+j;
            //pa_set(ds->b1, p, MOD(pa_get(ds->b1, p) + pa_get(c, p)));
            //pa_set(ds->b2, p, MOD(pa_get(ds->b2, p) - pa_get(c, p)));
            share_t cp = pa_iter_get(itr_c);
            pa_iter_set(itr_b1w, MOD(pa_iter_get(itr_b1r) + cp));
            pa_iter_set(itr_b2w, MOD(pa_iter_get(itr_b2r) - cp));
          }
        }
        pa_iter_flush(itr_b1w); pa_iter_free(itr_b1r);
        pa_iter_flush(itr_b2w); pa_iter_free(itr_b2r);
        pa_iter_free(itr_c);

        perm_free(c);

        if (_party == 0) {
            //mpc_send_channel(TO_PARTY1, ds->b1->B, pa_size(ds->b1), channel);    send_3 += pa_size(ds->b1);
            mpc_send_pa_channel(TO_PARTY1, ds->b1, channel);    //send_3 += pa_size(ds->b1);
            mpc_send_pa_channel(TO_PARTY2, ds->b2, channel);
        }
    }
    else {  // party 1, 2
        ds->a = pa_new(n*bs, k);
        ds->b = pa_new(n*bs, k);
        
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            int p = i*bs+j;
            pa_set(ds->a, p, RANDOM(mt_[FROM_SERVER][channel], q));
          }
        }
        mpc_recv_channel(FROM_SERVER, (char *)ds->b->B, pa_size(ds->b), channel);
    }
}
//#define block_dshare_correted_random(bs, ds) block_dshare_correlated_random_channel(bs, ds, 0)
#define dshare_correlated_random_channel(ds, channel) block_dshare_correlated_random_channel(ds, channel)
#define dshare_correlated_random(ds) dshare_correlated_random_channel(ds, 0)

static void dshare_correlated_random_xor_channel(dshare ds, int channel) {
  if (_party >  2) return;
    int bs = ds->bs;
    int n = ds->n;
    share_t q = ds->q;
    int k = blog(q - 1) + 1;
    if (_party <= 0) {
        ds->a1 = pa_new(n*bs, k);
        ds->a2 = pa_new(n*bs, k);
        perm c = pa_new(n*bs, k);

        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            pa_set(ds->a1, i*bs+j, RANDOM(mt_[TO_PARTY1][channel], q));
          }
        }
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            pa_set(ds->a2, i*bs+j, RANDOM(mt_[TO_PARTY2][channel], q));
          }
        }
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            pa_set(c, i*bs+j, RANDOM(mt_[0][0], q));
          }
        }
        ds->b1 = block_perm_apply(bs, ds->a2, ds->p1p);
        ds->b2 = block_perm_apply(bs, ds->a1, ds->p2p);

        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            int p = i*bs+j;
          //  pa_set(ds->b1, p, MOD(pa_get(ds->b1, p) + pa_get(c, p)));
          //  pa_set(ds->b2, p, MOD(pa_get(ds->b2, p) - pa_get(c, p)));
            pa_set(ds->b1, p, pa_get(ds->b1, p) ^ pa_get(c, p));
            pa_set(ds->b2, p, pa_get(ds->b2, p) ^ pa_get(c, p));
          }
        }

        perm_free(c);

        if (_party == 0) {
            mpc_send_pa_channel(TO_PARTY1, ds->b1, channel);    //send_3 += pa_size(ds->b1);
            mpc_send_pa_channel(TO_PARTY2, ds->b2, channel);
        }
    }
    else {  // party 1, 2
        ds->a = pa_new(n*bs, k);
        ds->b = pa_new(n*bs, k);
        
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            int p = i*bs+j;
            pa_set(ds->a, p, RANDOM(mt_[FROM_SERVER][channel], q));
          }
        }
        mpc_recv_channel(FROM_SERVER, (char *)ds->b->B, pa_size(ds->b), channel);
    }
}


///////////////////////////////////////////////////////////////////////////////////
// dshare をオンラインで計算する
// ds はここでは使わない
///////////////////////////////////////////////////////////////////////////////////
static dshare block_dshare_new2_channel(int bs, perm pi, share_t q, int channel) {
  if (_party >  2) return NULL;
    NEWT(dshare, ds);
    int n = pi->n;
    ds->n = n;
    ds->q = q;
    ds->bs = bs;
    if (_party <= 0) {
#if 0
        ds->pi = perm_id(n);
        for (int i = 0; i < n; ++i) {
            pa_set(ds->pi, i, pa_get(pi, i));
        }
#else
        ds->pi = pa_dup(pi);
#endif
        perm p1_inv, p2_inv;
        ds->p1 = perm_random(mt_[TO_PARTY1][channel], n);
        //printf("p1 "); perm_print(n, ds->p1);
        p1_inv = perm_inverse(ds->p1);
        //printf("p1_inv "); perm_print(n, p1_inv);
        ds->p2p = perm_apply(p1_inv, pi);
        //printf("p2p "); perm_print(n, ds->p2p);

        ds->p2 = perm_random(mt_[TO_PARTY2][channel], n);
        //printf("p2 "); perm_print(n, ds->p2);
        p2_inv = perm_inverse(ds->p2);
        //printf("p2_inv "); perm_print(n, p2_inv);
        ds->p1p = perm_apply(p2_inv, pi);
        //printf("p1p "); perm_print(n, ds->p1p);
        perm_free(p1_inv);
        perm_free(p2_inv);

        if (_party == 0) {
            mpc_send_pa_channel(TO_PARTY1, ds->p1p, channel);  //send_4 += pa_size(ds->p1p);
            mpc_send_pa_channel(TO_PARTY2, ds->p2p, channel);
        }
    } else {
        ds->g = perm_random(mt_[FROM_SERVER][channel], n);
        ds->gp = perm_id(n);
        //printf("gp size %d\n", pa_size(ds->gp));
        mpc_recv_channel(FROM_SERVER, (char *)ds->gp->B, pa_size(ds->gp), channel);
        //printf("gp "); perm_print(n, ds->gp);
    }

//    block_dshare_correlated_random_channel(bs, ds, channel);

    return ds;
}

///////////////////////////////////////////////////////////////////////////////////
// dshare をオフラインで計算する
// ds はここでは使わない
///////////////////////////////////////////////////////////////////////////////////
static dshare block_dshare_new_offline(int bs, perm pi, share_t q, int channel) 
{
    if (_party >  2) return NULL;
    NEWT(dshare, ds);
    int n = pi->n;
    ds->n = n;
    ds->q = q;
    ds->bs = bs;
    if (_party <= 0) {
        ds->pi = perm_id(n);
        for (int i = 0; i < n; ++i) {
            pa_set(ds->pi, i, pa_get(pi, i));
        }

        perm p1_inv, p2_inv;
        //ds->p1 = perm_random(mt1[0], n);
        ds->p1 = perm_random(mt_[TO_PARTY1][0], n);
        //printf("p1 "); perm_print(n, ds->p1);
        p1_inv = perm_inverse(ds->p1);
        //printf("p1_inv "); perm_print(n, p1_inv);
        ds->p2p = perm_apply(p1_inv, pi);
        //printf("p2p "); perm_print(n, ds->p2p);

        //ds->p2 = perm_random(mt2[0], n);
        ds->p2 = perm_random(mt_[TO_PARTY2][0], n);
        //printf("p2 "); perm_print(n, ds->p2);
        p2_inv = perm_inverse(ds->p2);
        //printf("p2_inv "); perm_print(n, p2_inv);
        ds->p1p = perm_apply(p2_inv, pi);
        //printf("p1p "); perm_print(n, ds->p1p);
        perm_free(p1_inv);
        perm_free(p2_inv);

    }

    block_dshare_correlated_random_channel(ds, channel);

    return ds;
}


///////////////////////////////////////////////////////////////////////////////////
// dshare をオンラインで計算する
///////////////////////////////////////////////////////////////////////////////////
static dshare block_dshare_new_channel(int bs, perm pi, share_t q, int channel)
{
  dshare ds = block_dshare_new2_channel(bs, pi, q, channel);
  block_dshare_correlated_random_channel(ds, channel);
  return ds;
}
#define dshare_new_channel(pi, q, channel) block_dshare_new_channel(1, pi, q, channel)
#define dshare_new(pi, q) dshare_new_channel(pi, q, 0)
#define block_dshare_new(bs, pi, q) block_dshare_new_channel(bs, pi, q, 0)

static dshare dshare_new_xor_channel(perm pi, share_t q, int channel)
{
  dshare ds = block_dshare_new2_channel(1, pi, q, channel);
  dshare_correlated_random_xor_channel(ds, channel);
  return ds;
}


static dshare block_dshare_new_party0(int bs, int n, share_t q)
{
  if (_party >  2) return NULL;

  NEWT(dshare, ds);
  ds->n = n;
  ds->q = q;
  ds->bs = bs;

  ds->pi = perm_id(n);

  perm p1_inv, p2_inv;
  ds->p1 = perm_id(n);
  ds->p2p = perm_id(n);

  ds->p2 = perm_id(n);
  ds->p1p = perm_id(n);


  int k = blog(q-1)+1;

  ds->a1 = pa_new(n*bs, k);
  ds->a2 = pa_new(n*bs, k);
  for (int i=0; i<n*bs; i++) {
    pa_set(ds->a1, i, 0);
  }
  for (int i=0; i<n*bs; i++) {
    pa_set(ds->a2, i, 0);
  }
  ds->b1 = block_perm_apply(bs, ds->a2, ds->p1p);
  ds->b2 = block_perm_apply(bs, ds->a1, ds->p2p);

  return ds;
}
#define dshare_new_party0(n, q) block_dshare_new_party0(1, n, q)

///////////////////////////////////////////
// 順列のみ生成．加える乱数は別に作る．
///////////////////////////////////////////
static dshare dshare_new2_channel(perm pi, share_t q, int channel)
{
  if (_party >  2) return NULL;
  int n = pi->n;
//  printf("Dshare2 n=%d q=%d\n", n, q);
  total_perm++;

  NEWT(dshare, ds);
  ds->n = n;
  ds->q = q;
  ds->bs = 1;
  if (_party <= 0) {
    ds->pi = perm_id(n);
    for (int i=0; i<n; i++) pa_set(ds->pi, i, pa_get(pi, i));

    perm p1_inv, p2_inv;
    ds->p1 = perm_random(mt_[TO_PARTY1][channel], n);
    p1_inv = perm_inverse(ds->p1);
    ds->p2p = perm_apply(p1_inv, pi);

    ds->p2 = perm_random(mt_[TO_PARTY2][channel], n);
    p2_inv = perm_inverse(ds->p2);
    ds->p1p = perm_apply(p2_inv, pi);
    perm_free(p1_inv);
    perm_free(p2_inv);

    mpc_send_pa_channel(TO_PARTY1, ds->p1p, channel);  //send_5 += pa_size(ds->p1p);
    mpc_send_pa_channel(TO_PARTY2, ds->p2p, channel);
  } else {
    ds->g = perm_random(mt_[FROM_SERVER][channel], n);
    ds->gp = perm_id(n);
    //mpc_recv_channel(FROM_SERVER, (char *)ds->gp->B, pa_size(ds->gp), channel);
    mpc_recv_pa_channel(FROM_SERVER, ds->gp, channel);
  }

  return ds;
}

#define dshare_new2(pi, q) dshare_new2_channel(pi, q, 0)

static void dshare_free(dshare ds)
{
  if (_party >  2) return;
  if (_party <= 0) {
    perm_free(ds->pi);
    perm_free(ds->p1);
    perm_free(ds->p1p);
    perm_free(ds->p2);
    perm_free(ds->p2p);
    perm_free(ds->a1);
    perm_free(ds->b1);
    perm_free(ds->a2);
    perm_free(ds->b2);
  } else {
    perm_free(ds->g);
    perm_free(ds->gp);
    perm_free(ds->a);
    perm_free(ds->b);
  }
  free(ds);
}

///////////////////////////////////////////
// 加える乱数以外を解放
///////////////////////////////////////////
static void dshare_free2(dshare ds)
{
  if (_party >  2) return;
  if (_party <= 0) {
    perm_free(ds->pi);
    perm_free(ds->p1);
    perm_free(ds->p1p);
    perm_free(ds->p2);
    perm_free(ds->p2p);
//    perm_free(ds->a1);
//    perm_free(ds->b1);
//    perm_free(ds->a2);
//    perm_free(ds->b2);
  } else {
    perm_free(ds->g);
    perm_free(ds->gp);
//    perm_free(ds->a);
//    perm_free(ds->b);
  }
  free(ds);
}

///////////////////////////////////////////
// 加える乱数のみを解放
///////////////////////////////////////////
static void dshare_free3(dshare ds)
{
  if (_party >  2) return;
  if (_party <= 0) {
    perm_free(ds->a1);
    perm_free(ds->b1);
    perm_free(ds->a2);
    perm_free(ds->b2);
  } else {
    perm_free(ds->a);
    perm_free(ds->b);
  }
}

/*************************************************************
def dshare_shuffle(X1, X2, p1, p2, p1p, p2p, a1, a2, a1p, a2p):
  n = len(X1)

# P1
  x1 = X1
  v1 = perm_apply(x1, p1)
  i = 0
  while i < n:
    v1[i] += a1[i]
    i += 1

# P2
  x2 = X2
  v2 = perm_apply(x2, p2)
  i = 0
  while i < n:
    v2[i] += a2[i]
    i += 1

# P1
  y1 = perm_apply(v2, p1p)
  i = 0
  while i < n:
    y1[i] -= a1p[i]
    i += 1

# P2
  y2 = perm_apply(v1, p2p)
  i = 0
  while i < n:
    y2[i] -= a2p[i]
    i += 1

  return (y1, y2)
*************************************************************/

/////////////////////////////////////////////////////////////////////////////////////////////
// dshare ds を用いて x を並び替える
/////////////////////////////////////////////////////////////////////////////////////////////
static share_array block_dshare_shuffle_channel(int bs, share_array x, dshare ds, int channel) {
  if (_party >  2) return NULL;
    if (bs != ds->bs) {
      printf("block_dshare_shuffle_channel: bs = %d ds->bs = %d\n", bs, ds->bs);
      exit(1);
    }
    share_t q = order(x);
    share_array v;
    int n = len(x) / bs;
    if (n != ds->n) {
        printf("block_dshare_shuffle_channel: n %d ds->n %d\n", n, ds->n);
        exit(EXIT_FAILURE);
    }

    if (_party <= 0) {
      v = block_share_perm(bs, x, ds->p1);
      // printf("v ok\n");   fflush(stdout);
#if 0
      for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
          int p = i*bs+j;
          pa_set(v->A, p, MOD(pa_get(v->A, p) + pa_get(ds->a1, p)));
        }
      }
#else
      pa_iter itr_vr = pa_iter_new(v->A);
      pa_iter itr_vw = pa_iter_new(v->A);
      pa_iter itr_a1 = pa_iter_new(ds->a1);
      for (int i = 0; i < n*bs; ++i) {
        pa_iter_set(itr_vw, MOD(pa_iter_get(itr_vr) + pa_iter_get(itr_a1)));
      }
      pa_iter_flush(itr_vw); pa_iter_free(itr_vr); pa_iter_free(itr_a1);
#endif
    } else {
        //printf("x:\n"); share_print(share_reconstruct(x));
        //printf("g "); perm_print(n, ds->g);
        v = block_share_perm(bs, x, ds->g);
        //printf("v:\n");share_print(share_reconstruct(v));
#if 0
        for (int i = 0; i < n; ++i) {
          for (int j = 0; j < bs; ++j) {
            int p = i*bs+j;
            pa_set(v->A, p, MOD(pa_get(v->A, p) + pa_get(ds->a, p)));
          }
        }
#else
      pa_iter itr_vr = pa_iter_new(v->A);
      pa_iter itr_vw = pa_iter_new(v->A);
      pa_iter itr_a = pa_iter_new(ds->a);
      for (int i = 0; i < n*bs; ++i) {
        pa_iter_set(itr_vw, MOD(pa_iter_get(itr_vr) + pa_iter_get(itr_a)));
      }
      pa_iter_flush(itr_vw); pa_iter_free(itr_vr); pa_iter_free(itr_a);
#endif
        //printf("v:\n");share_print(share_reconstruct(v));
    }

    share_array y;
    if (_party <= 0) {
      y = block_share_perm(bs, v, ds->p2p);
      perm tmp = block_perm_apply(bs, ds->a2, ds->p1p);
#if 0
      for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
          int p = i*bs+j;
          pa_set(y->A, p, MOD(pa_get(y->A, p) - pa_get(ds->b2, p)));
        }
      }
      for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
          int p = i*bs+j;
          pa_set(y->A, p, MOD(pa_get(y->A, p) + pa_get(tmp, p) - pa_get(ds->b1, p)));
        }
      }
#else
      pa_iter itr_yr = pa_iter_new(y->A);
      pa_iter itr_yw = pa_iter_new(y->A);
      pa_iter itr_b1 = pa_iter_new(ds->b1);
      pa_iter itr_b2 =pa_iter_new(ds->b2);
      pa_iter itr_tmp = pa_iter_new(tmp);
      for (int i = 0; i < n*bs; ++i) {
        pa_iter_set(itr_yw, MOD(pa_iter_get(itr_yr) + pa_iter_get(itr_tmp) - pa_iter_get(itr_b1) - pa_iter_get(itr_b2)));
      }
      pa_iter_flush(itr_yw); pa_iter_free(itr_yr); pa_iter_free(itr_b2); pa_iter_free(itr_b1); pa_iter_free(itr_tmp);
#endif
      perm_free(tmp);
        // send_8 += pa_size(v->a->A);
    } else {
      share_array z = share_dup(v);
      mpc_exchange_channel(v->A->B, z->A->B, pa_size(v->A), channel);
      //printf("exchange z: total send %ld\n", get_total_send());
      //printf("z "); _print_debug_channel(z, channel);
      //printf("gp "); perm_print(n, ds->gp);
      y = block_share_perm(bs, z, ds->gp);
      //printf("y\n");share_print(share_reconstruct(y));
#if 0
      for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
          int p = i*bs+j;
          pa_set(y->A, p, MOD(pa_get(y->A, p) - pa_get(ds->b, p)));
        }
      }
#else
      pa_iter itr_yr = pa_iter_new(y->A);
      pa_iter itr_yw = pa_iter_new(y->A);
      pa_iter itr_b = pa_iter_new(ds->b);
      for (int i = 0; i < n*bs; ++i) {
        pa_iter_set(itr_yw, MOD(pa_iter_get(itr_yr) - pa_iter_get(itr_b)));
      }
      pa_iter_flush(itr_yw); pa_iter_free(itr_yr); pa_iter_free(itr_b);
#endif
      //printf("y_raw\n");share_print(y);
      //printf("y\n");share_print(share_reconstruct(y));
      _free(z);
    }
    _free(v);

    return y;
}
#define block_dshare_shuffle(bs, x, ds) block_dshare_shuffle_channel(bs, x, ds, 0)
#define dshare_shuffle_channel(X, ds, channel) block_dshare_shuffle_channel(1, X, ds, channel)
#define dshare_shuffle(X, ds) dshare_shuffle_channel(X, ds, 0)


static share_array dshare_shuffle_xor_channel(share_array x, dshare ds, int channel) {
  if (_party >  2) return NULL;
  share_t q = order(x);
  share_array v;
  int n = len(x);
  if (n != ds->n) {
      printf("dshare_shuffle_xor_channel: n %d ds->n %d\n", n, ds->n);
      exit(EXIT_FAILURE);
  }

  if (_party <= 0) {
    v = share_perm(x, ds->p1);
    for (int i = 0; i < n; ++i) {
      pa_set(v->A, i, pa_get(v->A, i) ^ pa_get(ds->a1, i));
    }
  } else {
    v = share_perm(x, ds->g);
    for (int i = 0; i < n; ++i) {
      pa_set(v->A, i, pa_get(v->A, i) ^ pa_get(ds->a, i));
    }
  }

  share_array y;
  if (_party <= 0) {
    y = share_perm(v, ds->p2p);
    for (int i = 0; i < n; ++i) {
      pa_set(y->A, i, pa_get(y->A, i) ^ pa_get(ds->b2, i));
    }
    perm tmp = perm_apply(ds->a2, ds->p1p);
    for (int i = 0; i < n; ++i) {
      pa_set(y->A, i, pa_get(y->A, i) ^ pa_get(tmp, i) ^ pa_get(ds->b1, i));
    }
    perm_free(tmp);
  } else {
    share_array z = share_dup(v);
    mpc_exchange_channel(v->A->B, z->A->B, pa_size(v->A), channel);
    y = share_perm(z, ds->gp);
    for (int i = 0; i < n; ++i) {
      pa_set(y->A, i, pa_get(y->A, i) ^ pa_get(ds->b, i));
    }
    _free(z);
  }
  _free(v);

  return y;
}



static void check_dshare(dshare ds) {
  if (_party > 2) return;
  if (_party <= 0) {
  //  printf("pi:\n");perm_print(ds->n, ds->pi);
    packed_array p1_p2p = perm_apply(ds->p1, ds->p2p);
    packed_array p2_p1p = perm_apply(ds->p2, ds->p1p);
  //  printf("p1_p2p:\n");perm_print(p1_p2p->n, p1_p2p);
  //  printf("p2_p1p:\n");perm_print(p2_p1p->n, p2_p1p);

  }
  else {
    packed_array g_other = pa_new(ds->g->n, ds->g->w), gp_other = pa_new(ds->g->n, ds->g->w);
    mpc_exchange(ds->g->B, g_other->B, pa_size(g_other));
    mpc_exchange(ds->gp->B, gp_other->B, pa_size(gp_other));
    packed_array g_gp_other = perm_apply(ds->g, gp_other);
  //  printf("g_gp_other\n");perm_print(g_gp_other->n, g_gp_other);
    packed_array a_other = pa_new(ds->a->n, ds->a->w);
    mpc_exchange(ds->a->B, a_other->B, pa_size(a_other));
    
  }
}

typedef struct {
  int n;
  int bs;
  precomp_table PRG;
  precomp_table pp_1, b_1, pp_2, b_2;
  MMAP *map;
}* DS_tables;

typedef struct ds_tbl_list {
  DS_tables tbl;
  int n;
  int bs;
  int inverse;
  long count;
  struct ds_tbl_list *next;
}* ds_tbl_list;

ds_tbl_list PRE_DS_tbl[MAX_CHANNELS];
long PRE_DS_count[MAX_CHANNELS];


//////////////////////////////////////////////////
// dshare の計算 (事前計算)
// n: 順列の長さ
// m: 順列の個数
//////////////////////////////////////////////////
void DS_tables_precomp(int bs, int m, int n, share_t q, int inverse, char *fname)
{
  FILE *f0, *f1, *f2;

//  int kq = blog(q-1)+1;
  int kn = blog(n-1)+1;

  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);

  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");

  unsigned long init[5]={0x123, 0x234, 0x345, 0x456, 0};
  MT m0 = MT_init_by_array(init, 5);

  // party 1 が使う乱数
  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 0};
  init1[4] = 1; // rand();
  //mt1[0] = MT_init_by_array(init1, 5); // 注意 この関数は通常の計算中に使ってはならない
  mt_[TO_PARTY1][0] = MT_init_by_array(init1, 5); // 注意 この関数は通常の計算中に使ってはならない

  // party 2 が使う乱数
  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 0};
  init2[4] = 2; // rand();
  //mt2[0] = MT_init_by_array(init2, 5);
  mt_[TO_PARTY2][0] = MT_init_by_array(init2, 5);

  perm g = perm_random(m0, n);
  //perm g = perm_id(n);
  dshare ds1, ds2;
  share_t qq = max(1<<kn, q);

  if (inverse == 0) {
    perm g_inv = perm_inverse(g);
  //  ds1 = block_dshare_new(bs, g, 1<<kn); // 順列の方はブロックサイズは無関係 
  //  ds1 = block_dshare_new(1, g, 1<<kn); // 順列の方はブロックサイズは無関係
  //  ds2 = block_dshare_new(bs, g_inv, q);
    ds1 = block_dshare_new_offline(1, g, qq, 0); // 順列の方はブロックサイズは無関係
    ds2 = block_dshare_new_offline(bs, g_inv, qq, 0);
    perm_free(g_inv);
  } else {
  //  ds1 = block_dshare_new(bs, g, qq);
    ds1 = block_dshare_new_offline(1, g, qq, 0);
    ds2 = block_dshare_new_offline(bs, g, qq, 0);
  }
  perm_free(g);

  writeuint(sizeof(m), m, f1);
  writeuint(sizeof(m), m, f2);
  writeuint(sizeof(n), n, f1);
  writeuint(sizeof(n), n, f2);
  writeuint(sizeof(bs), bs, f1);
  writeuint(sizeof(bs), bs, f2);
//  precomp_write_seed(f1, n*2, qq, init1); // p1 と a1 を作るために 2n 個の乱数を使う
//  precomp_write_seed(f2, n*2, qq, init2); // p2 と a2
  precomp_write_seed(f1, n*(1+bs), qq, init1);
  precomp_write_seed(f2, n*(1+bs), qq, init2);
  precomp_write_pa(f1, ds1->p1p, qq);
  precomp_write_pa(f2, ds1->p2p, qq);
  precomp_write_pa(f1, ds1->b1, qq);
  precomp_write_pa(f2, ds1->b2, qq);
  precomp_write_pa(f1, ds2->p1p, qq);
  precomp_write_pa(f2, ds2->p2p, qq);
  precomp_write_pa(f1, ds2->b1, qq);
  precomp_write_pa(f2, ds2->b2, qq);

  MT_free(m0);
  dshare_free(ds1);
  dshare_free(ds2);

  fclose(f0);
  fclose(f1);
  fclose(f2);

  free(fname0);
  free(fname1);
  free(fname2);
}
#define block_dshare_precomp(bs, m, n, q, inverse, fname) DS_tables_precomp(bs, m, n, q, inverse, fname)
#define dshare_precomp(m, n, q, inverse, fname) block_dshare_precomp(1, m, n, q, inverse, fname)


void DS_tables_free(DS_tables T)
{
  if (T == NULL) return;
  if (_party >  2) return;
  if (_party < 0) return;
  precomp_free(T->PRG);
  precomp_free(T->pp_1);
  precomp_free(T->b_1);
  precomp_free(T->pp_2);
  precomp_free(T->b_2);
  if (T->map != NULL) mymunmap(T->map);
  free(T);
}

DS_tables DS_tables_read(char *fname)
{
//  if (_party >  2) return NULL;
//  if (_party <  0) return NULL;

  NEWT(DS_tables, T);

  if (_party <= 0 || _party > 2) {
    T->PRG = T->pp_1 = T->b_1 = T->pp_2 = T->b_2 = NULL;
    T->map = NULL;
    return T;
  }

  char *fname2 = precomp_fname(fname, _party);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  int m = getuint(p, 0, sizeof(int)); p += sizeof(int);
  T->n = getuint(p, 0, sizeof(int)); p += sizeof(int);
  T->bs = getuint(p, 0, sizeof(int)); p += sizeof(int);
  T->PRG = precomp_read(&p);
  T->pp_1 = precomp_read(&p);
  T->b_1 = precomp_read(&p);
  T->pp_2 = precomp_read(&p);
  T->b_2 = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}

#if 0
static void dshare_new_precomp0(DS_tables tbl, int n, share_t q_x, share_t q_sigma, dshare *ds1_, dshare *ds2_)
{
  if (_party >  2) return;
  if (_party <= 0) {
    dshare ds1 = dshare_new_party0(n, q_sigma);
    dshare ds2 = dshare_new_party0(n, q_x);
    *ds1_ = ds1;
    *ds2_ = ds2;
    return;
  }

/////////////////// ランダム順列
  NEWT(dshare, ds1);
  int k_sigma = blog(q_sigma-1)+1;
  ds1->n = n;
  ds1->q = q_sigma;

  ds1->g = perm_random(tbl->PRG->u.seed.r, n);
  ds1->gp = pa_new(n, k_sigma);
  for (int i=0; i<n; i++) {
    pa_set(ds1->gp, i, precomp_get(tbl->pp_1) % q_sigma);
  }
  //ds1->a = pa_new(n, k_x);
  ds1->a = pa_new(n, k_sigma);
  for (int i=0; i<n; i++) {
  //  pa_set(ds1->a, i, precomp_get(tbl->PRG) % q_x);
    pa_set(ds1->a, i, precomp_get(tbl->PRG) % q_sigma);
  }
  //ds1->b = pa_new(n, k_x);
  ds1->b = pa_new(n, k_sigma);
  for (int i=0; i<n; i++) {
  //  pa_set(ds1->b, i, precomp_get(tbl->b_1) % q_x);
    pa_set(ds1->b, i, precomp_get(tbl->b_1) % q_sigma);
  }

/////////////////// 値に加える乱数
  NEWT(dshare, ds2);
  int k_x = blog(q_x-1)+1;
  ds2->n = n;
  ds2->q = q_x;

  ds2->g = perm_random(tbl->PRG->u.seed.r, n);
  ds2->gp = pa_new(n, k_sigma);
  for (int i=0; i<n; i++) {
    pa_set(ds2->gp, i, precomp_get(tbl->pp_2) % q_sigma);
  }
  ds2->a = pa_new(n, k_x);
  for (int i=0; i<n; i++) {
    pa_set(ds2->a, i, precomp_get(tbl->PRG) % q_x);
  }
  ds2->b = pa_new(n, k_x);
  for (int i=0; i<n; i++) {
    pa_set(ds2->b, i, precomp_get(tbl->b_2) % q_x);
  }
  *ds1_ = ds1;  *ds2_ = ds2;
}
#endif

///////////////////////////////////////////////////////////////////
// 事前計算の表から取ってくる
// bs はデータのブロックサイズ．表 tbl のブロックサイズ以下ならば良い
////////////////////////////////////////////////////////////////////////
static void block_dshare_new_precomp(int bs, DS_tables tbl, int n, share_t q_x, share_t q_sigma, dshare *ds1_, dshare *ds2_)
{
  if (_party >  2) return;
  PRE_DS_count[0] += 1; // channel?
  if (_party <= 0) {
    dshare ds1 = dshare_new_party0(n, q_sigma);
    dshare ds2 = block_dshare_new_party0(bs, n, q_x);
    *ds1_ = ds1;
    *ds2_ = ds2;
    return;
  }

/////////////////// ランダム順列
  NEWT(dshare, ds1);
  int k_sigma = blog(q_sigma-1)+1;
  ds1->n = n;
  ds1->q = q_sigma;
  ds1->bs = 1;

  ds1->g = perm_random(tbl->PRG->u.seed.r, n);
  //printf("pre1 g "); perm_print(n, ds1->g);
  ds1->gp = pa_new(n, k_sigma);
  pa_iter itr;
  itr = pa_iter_new(ds1->gp);
  for (int i=0; i<n; i++) {
    //pa_set(ds1->gp, i, precomp_get(tbl->pp_1) % q_sigma);
    pa_iter_set(itr, precomp_get(tbl->pp_1) % q_sigma);
  }
  pa_iter_flush(itr);
  //printf("pre gp "); perm_print(n, ds1->gp);
  //ds1->a = pa_new(n, k_x);
  ds1->a = pa_new(n, k_sigma);
  itr = pa_iter_new(ds1->a);
  for (int i=0; i<n; i++) {
    //pa_set(ds1->a, i, precomp_get(tbl->PRG) % q_sigma);
    pa_iter_set(itr, precomp_get(tbl->PRG) % q_sigma);
  }
  pa_iter_flush(itr);
  //ds1->b = pa_new(n, k_x);
  ds1->b = pa_new(n, k_sigma);
  itr = pa_iter_new(ds1->b);
  for (int i=0; i<n; i++) {
    //pa_set(ds1->b, i, precomp_get(tbl->b_1) % q_sigma);
    pa_iter_set(itr, precomp_get(tbl->b_1) % q_sigma);
  }
  pa_iter_flush(itr);

/////////////////// 値に加える乱数
  NEWT(dshare, ds2);
  int k_x = blog(q_x-1)+1;
  ds2->n = n;
  ds2->q = q_x;
//  ds2->bs = tbl->bs;
  ds2->bs = bs;

  ds2->g = perm_random(tbl->PRG->u.seed.r, n);
  //printf("pre2 g "); perm_print(n, ds2->g);
  ds2->gp = pa_new(n, k_sigma);
  itr = pa_iter_new(ds2->gp);
  for (int i=0; i<n; i++) {
    //pa_set(ds2->gp, i, precomp_get(tbl->pp_2) % q_sigma);
    pa_iter_set(itr, precomp_get(tbl->pp_2) % q_sigma);
  }
  pa_iter_flush(itr);
  //printf("pre2 gp "); perm_print(n, ds2->gp);
  //NEWT(share_t*, ptmp);
  share_t *ptmp;
  NEWA(ptmp, share_t, tbl->bs);
  ds2->a = pa_new(n*bs, k_x);
  itr = pa_iter_new(ds2->a);
  for (int i=0; i<n; i++) {
    for (int j=0; j<tbl->bs; j++) {
      ptmp[j] = precomp_get(tbl->PRG) % q_x;
    }
    for (int j=0; j<bs; j++) {
      int j2 = j % tbl->bs; // 表が足りないときは使いまわす (本当はダメ)
      //pa_set(ds2->a, i*bs+j, ptmp[j2]);
      pa_iter_set(itr, ptmp[j2]);
    }
  }
  pa_iter_flush(itr);
  ds2->b = pa_new(n*bs, k_x);
  itr = pa_iter_new(ds2->b);
  for (int i=0; i<n; i++) {
    for (int j=0; j<tbl->bs; j++) {
      ptmp[j] = precomp_get(tbl->b_2) % q_x;
    }
    for (int j=0; j<bs; j++) {
      int j2 = j % tbl->bs; // 表が足りないときは使いまわす (本当はダメ)
      //pa_set(ds2->b, i*bs+j, ptmp[j2]);
      pa_iter_set(itr, ptmp[j2]);
    }
  }
  pa_iter_flush(itr);
  free(ptmp);
  *ds1_ = ds1;  *ds2_ = ds2;
}
#define dshare_new_precomp(tbl, n, q_x, q_sigma, ds1_, ds2_) block_dshare_new_precomp(1, tbl, n, q_x, q_sigma, ds1_, ds2_)

ds_tbl_list ds_tbl_list_insert(DS_tables tbl, int n, int bs, int inverse, ds_tbl_list head)
{
  NEWT(ds_tbl_list, list);
  list->tbl = tbl;
  list->n = n;
  list->bs = bs;
  list->inverse = inverse;
  list->count = 0;
  list->next = head;
  return list;
}

////////////////////////////////////////////////////////////////////////
// 長さ n の順列の dshare を返す
////////////////////////////////////////////////////////////////////////
DS_tables ds_tbl_list_search(ds_tbl_list list, int inverse, int n)
{
  DS_tables ans = NULL;
  while (list != NULL) {
  //  printf("list n %d inverse %d\n", list->n, list->inverse);
    if (list->tbl->n == n && list->inverse == inverse) {
      ans = list->tbl;
      break;
    }
    list = list->next;
  }
  return ans;
}

////////////////////////////////////////////////////////////////////////
// n 以上の長さの順列の dshare を返す
////////////////////////////////////////////////////////////////////////
DS_tables ds_tbl_list_search2(ds_tbl_list list, int inverse, int n)
{
  DS_tables ans = NULL;
  while (list != NULL) {
    //printf("list n %d inverse %d\n", list->n, list->inverse);
    if ((list->n >= n) && (list->n < n*2) && (list->inverse == inverse)) {
      ans = list->tbl;
      break;
    }
    list = list->next;
  }
  return ans;
}

void ds_tbl_list_free(ds_tbl_list list)
{
  ds_tbl_list next;
  while (list != NULL) {
    next = list->next;
    DS_tables_free(list->tbl);
    free(list);
    list = next;
  }
}

void ds_tbl_init(void)
{
  for (int i=0; i<_opt.channels; i++) {
    PRE_DS_tbl[i] = NULL;
    PRE_DS_count[i] = 0;
  }
}

void ds_tbl_read(int channel, int n, int bs, int inverse, char *fname)
{
  DS_tables tbl = DS_tables_read(fname);
  tbl->n = n; // test
  PRE_DS_tbl[channel] = ds_tbl_list_insert(tbl, n, bs, inverse, PRE_DS_tbl[channel]);
  //PRE_DS_tbl[0] = ds_tbl_list_insert(tbl, n, bs, inverse, PRE_DS_tbl[0]); // temp
}

//////////////////////////////////////////////////////////////////////////////////////////
// 長さ n の順列を，長さ n2 > n の順列に埋め込んで，事前計算したものを用いる
//////////////////////////////////////////////////////////////////////////////////////////
static share_array block_AppPerm_fwd_offline_channel(DS_tables tbl, int bs, share_array x, share_array sigma, int channel)
{
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
  dshare ds1;
  dshare ds2;
  //printf("block_AppPerm_fwd_offline_channel: tbl->n %d bs %d len(x) %d len(sigma) %d\n", tbl->n, bs, len(x), len(sigma));
  int n2 = tbl->n;
  int n = len(x) / bs;
  //printf("n %d n2 %d order %d\n", n, n2, order(sigma));
  int k = blog(n2-1)+1;
  _ sigma2 = _const(n2, 0, 1<<k);
  for (int i=0; i<n; i++) {
    pa_set(sigma2->A, i, pa_get(sigma->A, i) % (1<<k));
  }
  for (int i=n; i<n2; i++) _setpublic(sigma2, i, i);
  _ x2 = _const(n2*bs, 0, order(x));
  _setshares(x2, 0, n*bs, x, 0);
  for (int i=n*bs; i<n2*bs; i++) _setpublic(x2, i, 0);
  block_dshare_new_precomp(bs, tbl, n2, order(x2), order(sigma2), &ds1, &ds2);

  _ w;
  _ rho = dshare_shuffle_channel(sigma2, ds1, channel);
  //printf("rho: total send %ld\n", get_total_send());
  if (_party <= 0) {
      w = block_share_perm(bs, x2, share_raw(rho));
      // send_5 += pa_size(w->A);
  } else {
    _ r = share_reconstruct_channel(rho, channel);
    //printf("r: total send %ld\n", get_total_send());
    w = block_share_perm(bs, x2, share_raw(r));
    //printf("w: total send %ld\n", get_total_send());
    _free(r);
  }

  _ ans0 = block_dshare_shuffle_channel(bs, w, ds2, channel);
  //printf("ans0: total send %ld\n", get_total_send());
  _ ans = _slice(ans0, 0, n*bs);

  dshare_free(ds1);
  dshare_free(ds2);
  _free(rho);
  _free(w);
  _free(sigma2);
  _free(x2);
  _free(ans0);
    
  return ans;
}

//////////////////////////////////////////////////////////////////////////////////////////
// 長さ n の順列を，長さ n2 > n の順列に埋め込んで，事前計算したものを用いる
//////////////////////////////////////////////////////////////////////////////////////////
static share_array block_AppPerm_inverse_offline_channel(DS_tables tbl, int bs, share_array x, share_array sigma, int channel)
{
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
  dshare ds1;
  dshare ds2;
//  printf("block_AppPerm_inverse_offline_channel: tbl->n %d bs %d len(x) %d len(sigma) %d\n", tbl->n, bs, len(x), len(sigma));
  int n2 = tbl->n;
  int n = len(x) / bs;
  int k = blog(n2-1)+1;
  _ sigma2 = _const(n2, 0, 1<<k);
  for (int i=0; i<n; i++) {
    pa_set(sigma2->A, i, pa_get(sigma->A, i) % (1<<k));
  }
  for (int i=n; i<n2; i++) _setpublic(sigma2, i, i);
  _ x2 = _const(n2*bs, 0, order(x));
  _setshares(x2, 0, n*bs, x, 0);
  for (int i=n*bs; i<n2*bs; i++) _setpublic(x2, i, 0);
  //printf("2:x  ");     share_print(_reconstruct(x));  fflush(stdout);
  //printf("2:x2 ");     share_print(_reconstruct(x2));  fflush(stdout);
  block_dshare_new_precomp(bs, tbl, n2, order(x2), order(sigma2), &ds1, &ds2);

  _ rho = dshare_shuffle_channel(sigma2, ds1, channel);
//  printf("rho2 ");  share_print(_reconstruct(rho));  fflush(stdout);
  //printf("rho2 ");  share_print(rho);  fflush(stdout);
  //_ rtmp = share_reconstruct(rho);  // send_6 += pa_size(r->A);
  //printf("rtmp   ");  share_print(rtmp);    fflush(stdout);
  _ z = block_dshare_shuffle_channel(bs, x2, ds2, channel);
  //printf("z   "); _print_debug(z);  fflush(stdout);
  _ r = share_reconstruct_channel(rho, channel);  // send_6 += pa_size(r->A);
  //printf("r2   ");  share_print(r);    fflush(stdout);
  perm rho_inv = perm_inverse(share_raw(r));
  //printf("rho_inv ");  perm_print(n2*bs, rho_inv);
  //printf("rho_inv ");  perm_print(r->A->n, rho_inv);
  _ ans0 = block_share_perm(bs, z, rho_inv);
  //printf("ans0 "); share_print(_reconstruct(ans0));  fflush(stdout);
  _ ans = _slice(ans0, 0, n*bs);
  //printf("ans2 "); share_print(_reconstruct(ans));  fflush(stdout);

  _free(r);
  _free(z);
  perm_free(rho_inv);
  _free(rho);
  dshare_free(ds1);
  dshare_free(ds2);
  _free(sigma2);
  _free(x2);
  _free(ans0);
    
  return ans;
}

////////////////////////////////////////////////////////////////////////////////////////////
// 事前計算の表があれば用い，無ければオンラインで計算する
////////////////////////////////////////////////////////////////////////////////////////////
static share_array block_AppPerm_fwd_channel(int bs, share_array x, share_array sigma, int channel)
{
  //if (_party >  2) return NULL;
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
    int n = len(x) / bs;
    if (n != len(sigma)) {
        printf("block_AppPerm_fwd_channel: block_len(x) %d len(sigma) %d\n", n, len(sigma));
    }
    dshare ds1;
    dshare ds2;

    // printf("AppPerm_fwd n = %d\n", n);

    DS_tables tbl;

    if (tbl = ds_tbl_list_search2(PRE_DS_tbl[channel], 0, n)) {
    //if (tbl = ds_tbl_list_search2(PRE_DS_tbl[0], 0, n)) { // temp
      //printf("bs: %d\n", tbl->bs);
      int n2 = tbl->n;
      //printf("using DS_table n = %d n2 = %d\n", n, n2);
      if (n2 >= n) {
        return block_AppPerm_fwd_offline_channel(tbl, bs, x, sigma, channel);
      } else {//printf("n == n2\n");
        block_dshare_new_precomp(bs, tbl, n, order(x), order(sigma), &ds1, &ds2);
      }
    } else {
        if (_opt.warn_precomp) printf("without DS_table n = %d\n", n);
        perm g;
        if (_party == 0) {
            //g = perm_random(mt0, n);
            g = perm_random(mt_[0][channel], n);
        } else {
            g = perm_id(n);
        }
        perm g_inv = perm_inverse(g);

        ds1 = dshare_new_channel(g, order(sigma), channel);
        ds2 = block_dshare_new_channel(bs, g_inv, order(x), channel);
        perm_free(g_inv);
        perm_free(g);
    }
    // ここまでが前計算
  //  check_dshare(ds1); // なにこれ？
  //  check_dshare(ds2);

    _ w;
    _ rho = dshare_shuffle_channel(sigma, ds1, channel);
#if 0
    // ここから一時的なコード
    _ S = share_reconstruct(sigma);
    // printf("sigma\n");
    // share_print(S);
    // printf("correlated randomness\n");
    _ R = share_reconstruct(rho);
    // printf("rho\n");
    // share_print(R);
    // ここまで一時的なコード
#endif
    if (_party <= 0) {
        w = block_share_perm(bs, x, share_raw(rho));
        // send_5 += pa_size(w->A);
    }
    else {
        _ r = share_reconstruct_channel(rho, channel);
        w = block_share_perm(bs, x, share_raw(r));
        //ここから
      //  _ W = share_reconstruct(w);
      //  printf("w\n");
      //  share_print(W);
        //ここまで
        _free(r);
    }

    _ ans = block_dshare_shuffle_channel(bs, w, ds2, channel);

    dshare_free(ds1);
    dshare_free(ds2);
    _free(rho);
    _free(w);
    
    return ans;
}
#define block_AppPerm_fwd(bs, x, sigma) block_AppPerm_fwd_channel(bs, x, sigma, 0)
#define AppPerm_fwd_channel(x, sigma, channel) block_AppPerm_fwd_channel(1, x, sigma, channel)
#define AppPerm_fwd(x, sigma) AppPerm_fwd_channel(x, sigma, 0)


static share_array AppPerm_fwd_xor_channel(share_array x, share_array sigma, int channel)
{
  //if (_party >  2) return NULL;
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
  int n = len(x);
  if (n != len(sigma)) {
    printf("AppPerm_fwd_xor_channel: len(x) %d len(sigma) %d\n", n, len(sigma));
  }
  dshare ds1;
  dshare ds2;

  perm g;
  if (_party == 0) {
    //g = perm_random(mt0, n);
    g = perm_random(mt_[0][channel], n);
  } else {
    g = perm_id(n);
  }
  perm g_inv = perm_inverse(g);

  ds1 = dshare_new_channel(g, order(sigma), channel);
  ds2 = dshare_new_xor_channel(g_inv, order(x), channel);
  perm_free(g_inv);
  perm_free(g);

  // ここまでが前計算
  //check_dshare(ds1);
  //check_dshare(ds2);

  _ w;
  _ rho = dshare_shuffle_channel(sigma, ds1, channel);
  if (_party <= 0) {
    w = share_perm(x, share_raw(rho));
  } else {
    _ r = share_reconstruct_channel(rho, channel);
    w = share_perm(x, share_raw(r));
    _free(r);
  }

  _ ans = dshare_shuffle_xor_channel(w, ds2, channel);

  dshare_free(ds1);
  dshare_free(ds2);
  _free(rho);
  _free(w);
    
  return ans;
}

//static share_array block_AppPerm_channel(int bs, _ x, _ sigma, int channel) {
//  if (_party >  2) return NULL;
//  _ ans = block_AppPerm_fwd_channel(bs, x, sigma, channel);
//  return ans;
//}
#define block_AppPerm(bs, x, sigma) block_AppPerm_fwd_channel(bs, x, sigma, 0)

static void block_AppPerm_channel_(int bs, _ x, _ sigma, int channel) {
  //if (_party >  2) return;
  _ ans = block_AppPerm_fwd_channel(bs, x, sigma, channel);
  _move_(x, ans);
}
#define block_AppPerm_(bs, x, sigma) block_AppPerm_channel_(bs, x, sigma, 0)

////////////////////////////////////////////////////////////////////////////////////////////
// 事前計算の表があれば用い，無ければオンラインで計算する
////////////////////////////////////////////////////////////////////////////////////////////
static share_array block_AppPerm_inverse_channel(int bs, share_array x, _ sigma, int channel) {
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
    int n = len(x) / bs;
    if (n != len(sigma)) {
        printf("block_AppPerm_inverse: block_len(x) %d len(sigma) %d\n", n, len(sigma));
    }

    //printf("AppPerm_inverse n = %d\n", n);

    dshare ds1;
    dshare ds2;

    DS_tables tbl;

    int ln = blog(n-1) + 1;
    if (tbl = ds_tbl_list_search2(PRE_DS_tbl[channel], 1, n)) {
    //if (tbl = ds_tbl_list_search2(PRE_DS_tbl[0], 1, n)) { // temp
      int n2 = tbl->n;
      //printf("using DSi_table n = %d n2 = %d\n", n, n2);
      if (n2 >= n) {
        return block_AppPerm_inverse_offline_channel(tbl, bs, x, sigma, channel);
      } else {
        block_dshare_new_precomp(bs, tbl, n, order(x), order(sigma), &ds1, &ds2);
      }
    } else {
        if (_opt.warn_precomp) printf("without DSi_table n = %d\n", n);
        perm g;
        if (_party == 0) {
            //g = perm_random(mt0, n);
            g = perm_random(mt_[0][channel], n);
        } else {
            g = perm_id(n);
        }

        ds1 = dshare_new_channel(g, order(sigma), channel);
        ds2 = block_dshare_new_channel(bs, g, order(x), channel);
        
        perm_free(g);
    }
    // ここまでが前計算

    _ rho = dshare_shuffle_channel(sigma, ds1, channel);
    //printf("rho ");  share_print(_reconstruct(rho));  fflush(stdout);
    share_array z = block_dshare_shuffle_channel(bs, x, ds2, channel);
    //printf("z   "); _print_debug_channel(z, channel);  fflush(stdout);
    _ r = share_reconstruct_channel(rho, channel);  // send_6 += pa_size(r->A);
    //printf("r   ");  share_print(r);    fflush(stdout);
    perm rho_inv = perm_inverse(share_raw(r));
    //printf("rho_inv ");  perm_print(len(z), rho_inv);    fflush(stdout);
    share_array ans = block_share_perm(bs, z, rho_inv);
    //printf("ans "); share_print(_reconstruct(ans));  fflush(stdout);
    _free(r);
    _free(z);
    perm_free(rho_inv);
    _free(rho);
    dshare_free(ds1);
    dshare_free(ds2);

    return ans;
}
#define AppPerm_inverse_channel(x, sigma, channel) block_AppPerm_inverse_channel(1, x, sigma, channel)

static share_array AppPerm_inverse_xor_channel(share_array x, _ sigma, int channel) {
  //if (_party >  2) return NULL;
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
  int n = len(x);
  if (n != len(sigma)) {
    printf("AppPerm_inverse_xor: len(x) %d len(sigma) %d\n", n, len(sigma));
  }

  dshare ds1;
  dshare ds2;

  perm g;
  if (_party == 0) {
    //g = perm_random(mt0, n);
    g = perm_random(mt_[0][channel], n);
  } else {
    g = perm_id(n);
  }

  ds1 = dshare_new_channel(g, order(sigma), channel);
  ds2 = dshare_new_xor_channel(g, order(x), channel);
        
  perm_free(g);
  // ここまでが前計算

  _ rho = dshare_shuffle_channel(sigma, ds1, channel);
  share_array z = dshare_shuffle_xor_channel(x, ds2, channel);
  _ r = share_reconstruct_channel(rho, channel);  // send_6 += pa_size(r->A);
  perm rho_inv = perm_inverse(share_raw(r));
  share_array ans = share_perm(z, rho_inv);
  _free(r);
  _free(z);
  perm_free(rho_inv);
  _free(rho);
  dshare_free(ds1);
  dshare_free(ds2);

  return ans;
}



static void block_AppInvPerm_channel_(int bs, share_array x, _ sigma, int channel) {
  //if (_party >  2) return;
    share_array ans = block_AppPerm_inverse_channel(bs, x, sigma, channel);
    _move_(x, ans);
}
#define block_AppInvPerm_(bs, x, sigma) block_AppInvPerm_channel_(bs, x, sigma, 0)


/*****************************************************************
def AppPerm(x, sigma):
  print("AppPerm x", x, "sigma", sigma)
  n = len(x)
  if n != len(sigma):
    print("AppPerm len(x)", len(x), "len(sigma)", len(sigma))
  g = perm_random(n)
#  g = Perm_ID(n)
  print("AppPerm g", g)
  (p1, pi_inv, p2p, p2, p2_inv, p1p) = dshare_new(g)
  (a1, a2, b1, b2, c) = dshare_correlated_random(p1p, p2p)
  X1 = [None] * n
  X2 = [None] * n
  i = 0
  while i < n:
    X1[i] = random.randint(0, n-1)
    X2[i] = sigma[i] - X1[i]
    i = i+1
  (y1, y2) = dshare_shuffle(X1, X2, p1, p2, p1p, p2p, a1, a2, b1, b2)
  y = [None] * n
  i = 0
  while i < n:
    y[i] = (y1[i]+y2[i]) % n
    i = i+1
  print("AppPerm y", y)
  w = perm_apply(x, y)
  g_inv = perm_inverse(g)
  w2 = perm_apply(w, g_inv)
  print("AppPerm w2", w2)
#  y_ = AppPerm_(x, sigma)
#  print("AppPerm_ y", y_)
#  return y_
  return w2
*****************************************************************/

///////////////////////////////////////////////////////////////////////////////////
// オンラインで計算する場合のメイン (bits版)
///////////////////////////////////////////////////////////////////////////////////
static _bits AppPerm_new_bits_channel(_bits x, _ sigma, int inverse, int channel)
{
  if (_party >  2) return NULL;
  dshare ds;
  int d = x->d;
//  printf("AppPerm sigma:"); share_print(sigma);
//  printf("AppPerm x:"); share_print(x);
//  printf("sigma k=%d\n", sigma->A->w);
//  printf("x k=%d\n", x->A->w);
  int n = len(x->a[0]);
  if (n != len(sigma)) {
    printf("AppPerm: len(x) = %d len(sigma) = %d", len(x->a[0]), len(sigma));
  }
  perm g;
  if (_party == 0) {
  //  g = perm_random(n);
    //g = perm_random(mt0, n);
    g = perm_random(mt_[0][channel], n);
  } else {
    g = perm_id(n);
  }
//  printf("g "); perm_print(g);

  //_ z;
  NEWT(_bits, z);
  NEWA(z->a, _, d);
  z->d = d;
  //_ w;
  NEWT(_bits, w);
  NEWA(w->a, _, d);
  w->d = d;

  ds = dshare_new_channel(g, order(sigma), channel);
  _ rho = dshare_shuffle_channel(sigma, ds, channel);
  dshare_free(ds);

  if (inverse) {
    dshare ds_x = dshare_new2_channel(g, order(x->a[0]), channel);
    for (int i=0; i<d; i++) {
      dshare_correlated_random_channel(ds_x, channel);
      z->a[i] = dshare_shuffle_channel(x->a[i], ds_x, channel);
      dshare_free3(ds_x);
    }
    dshare_free2(ds_x);
//    printf("AppInvPerm z:"); share_print(z);
  } else {
    if (_party <= 0) {
    //  printf("rho k=%d\n", rho->A->w);
    //  w = share_perm_bits(x, share_raw(rho));
      for (int i=0; i<d; i++) {
        w->a[i] = share_perm(x->a[i], share_raw(rho));
      }
    } else {
      _ r = _reconstruct_channel(rho, channel);
      //_save(r, "tmp_r");
      //w = share_perm_bits(x, share_raw(r));
      for (int i=0; i<d; i++) {
        w->a[i] = share_perm(x->a[i], share_raw(r));
      }
      _free(r);
    }
//    printf("AppPerm w:"); share_print(w);
  }


  //_ ans;
  NEWT(_bits, ans);
  NEWA(ans->a, _, d);
  ans->d = d;
  if (inverse == 0) {
    perm g_inv = perm_inverse(g);
  //  printf("g_inv "); perm_print(g_inv);
    ds = dshare_new2_channel(g_inv, order(w->a[0]), channel);

    //ans = dshare_shuffle_bits(w, ds);
    for (int i=0; i<d; i++) {
      dshare_correlated_random_channel(ds, channel);
      ans->a[i] = dshare_shuffle_channel(w->a[i], ds, channel);
      dshare_free3(ds);
    }
    dshare_free2(ds);
//    printf("AppPerm w2:"); share_print(w2);

    perm_free(g_inv);

  } else {
    _ r = _reconstruct_channel(rho, channel);
    perm rho_inv = perm_inverse(share_raw(r));
    //ans = share_perm_bits(z, rho_inv);
    for (int i=0; i<d; i++) {
      ans->a[i] = share_perm(z->a[i], rho_inv);
    }
    _free(r);
    //_free(z);
    //_free_bits(z);
    perm_free(rho_inv);
  }

  perm_free(g);
  _free(rho);
//  if (inverse == 0) _free(w);
  if (inverse == 0) _free_bits(w);
  free(z);

  return ans;
}
#define AppPerm_new_bits(x, sigma, inverse) AppPerm_new_bits_channel(x, sigma, inverse, 0)

_ Bits_to_block(_bits x)
{
  int n = len(x->a[0]);
  int d = x->d;
//  _ ans = _const(n*d, 0, order(x->a[0]));
  _ ans = share_const_type2(n*d, 0, order(x->a[0]), x->a[0]->type, x->a[0]->A->type);
  for (int j=0; j<d; j++) {
    _ b = x->a[j];
    for (int i=0; i<n; i++) {
      _setshare(ans, i*d+j, b, i);
    }
  }
  return ans;
}

_bits block_to_Bits(int bs, _ b)
{
  int n = len(b) / bs;
  NEWT(_bits, ans);
  NEWA(ans->a, _, bs);
  ans->d = bs;
  for (int j=0; j<bs; j++) {
    ans->a[j] = share_const_type2(n, 0, order(b), b->type, b->A->type);
    for (int i=0; i<n; i++) {
      _setshare(ans->a[j], i, b, i*bs+j);
    }
  }
  return ans;
}

typedef struct {
  int m; // まとめたシェアの個数
  int n; // それぞれのシェアの要素数
  int *d; // 元のシェア (Bits) の深さ
  share_t *org_q; // 元の位数

  _ B; // まとめたもの
  int bs;
  share_t q; // 元の位数の最大値
}* _block;

_block multi_Bits_to_block(int m, _bits *x)
{
  NEWT(_block, B);
  B->m = m;
  int n = len_bits(x[0]);
  B->n = n;
  NEWA(B->d, int, m);
  int block_size = 0;
  int bs = 0;
  for (int i=0; i<m; i++) {
    B->d[i] = depth_bits(x[i]);
    bs += B->d[i];
  }
  B->bs = bs;
  NEWA(B->org_q, share_t, bs);

  int p = 0;
  share_t q = 0;
  for (int i=0; i<m; i++) {
    for (int d=0; d<depth_bits(x[i]); d++) {
      share_t q_tmp = order(x[i]->a[d]);
      if (q_tmp > q) q = q_tmp;
      B->org_q[p++] = q_tmp;
    }
  }
  B->q = q;

  B->B = _const(n * bs, 0, q);
  pa_iter itr_B = pa_iter_new(B->B->A);
  pa_iter *itr;
  NEWA(itr, pa_iter, bs);
  p = 0;
  for (int i=0; i<m; i++) {
    for (int d=0; d<depth_bits(x[i]); d++) {
      itr[p++] = pa_iter_new(x[i]->a[d]->A);
    }
  }
  for (int j=0; j<n; j++) {
    for (int p=0; p<bs; p++) {
      pa_iter_set(itr_B, pa_iter_get(itr[p]));
    }
  }
  pa_iter_flush(itr_B);
  for (int i=0; i<bs; i++) pa_iter_free(itr[i]);
  free(itr);

  return B;
}

_bits* block_to_multi_Bits(_block B)
{
  int m = B->m;
  int n = B->n;
  int bs = B->bs;
  _bits* ans;
  NEWA(ans, _bits, m);

  pa_iter itr_B = pa_iter_new(B->B->A);
  pa_iter *itr;
  NEWA(itr, pa_iter, bs);

  int p;
  p = 0;
  for (int i=0; i<m; i++) {
    int depth = B->d[i];
    ans[i] = (_bits)malloc(sizeof(*ans[i]));
    if (ans[i] == NULL) {
      printf("malloc failed\n");
      exit(1);
    }
    NEWA(ans[i]->a, _, depth);
    ans[i]->d = depth;
    for (int d=0; d<depth; d++) {
      ans[i]->a[d] = _const(n, 0, B->org_q[p]);
      itr[p] = pa_iter_new(ans[i]->a[d]->A);
      p++;
    }
  }

  for (int j=0; j<n; j++) {
    p = 0;
    for (int i=0; i<m; i++) {
      for (int d=0; d<B->d[i]; d++) {
        share_t x = pa_iter_get(itr_B);
        share_t q = order(ans[i]->a[d]);
        pa_iter_set(itr[p++], x % q);
      }
    }
  }
  pa_iter_free(itr_B);
  for (int i=0; i<bs; i++) pa_iter_flush(itr[i]);
  free(itr);

  return ans;
}

void block_free(_block B)
{
  _free(B->B);
  free(B->d);
  free(B->org_q);
  free(B);
}

////////////////////////////////////////////
// シェアを深さ 1 のビット分解したものに変換
// 元の変数は以後使用できない
////////////////////////////////////////////
_bits share_to_bits(_ a)
{
  NEWT(_bits, ans);
  NEWA(ans->a, _, 1);
  ans->d = 1;
  ans->a[0] = a;

  return ans;
}

_ bits_to_share(_bits b)
{
  _ ans = _B2A_bits(b);
  _free_bits(b);
  return ans;
}

_ bits_shrink(_bits b)
{
  int d = b->d;
  int n = len_bits(b);
  _ ans = _const(d * n, 0, order_bits(b));
  pa_iter *itr_b;
  NEWA(itr_b, pa_iter, d);
  for (int i=0; i<d; i++) {
    itr_b[i] = pa_iter_new(b->a[i]->A);
  }
  pa_iter itr_ans = pa_iter_new(ans->A);
  for (int i=0; i<n; i++) {
    for (int j=0; j<d; j++) {
      pa_iter_set(itr_ans, pa_iter_get(itr_b[j]));
    }
  }
  pa_iter_flush(itr_ans);
  for (int i=0; i<d; i++) {
    pa_iter_free(itr_b[i]);
  }
  free(itr_b);
  _free_bits(b);

  return ans;
}

//_ IfThen_b(_ c, _ x);
//_ extend_share_array(int l, _ x);

_block IfThen_b_block(_ c, _block B)
{
  NEWT(_block, ans);
  *ans = *B;
  NEWA(ans->d, int, ans->m);
  NEWA(ans->org_q, share_t, ans->bs);
  for (int i=0; i<ans->m; i++) ans->d[i] = B->d[i];
  for (int i=0; i<ans->bs; i++) ans->org_q[i] = B->org_q[i];
  _ extended_c = extend_share_array(ans->bs, c);
  ans->B = IfThen_b(extended_c, B->B);
  _free(extended_c);
  return ans;
}

_ IfThenElse_channel(_ f, _ a, _ b, int channel);

_block IfThenElse_b_block(_ c, _block B_true, _block B_false)
{
  NEWT(_block, ans);
  *ans = *B_true;
  NEWA(ans->d, int, ans->m);
  NEWA(ans->org_q, share_t, ans->bs);
  for (int i=0; i<ans->m; i++) ans->d[i] = B_true->d[i];
  for (int i=0; i<ans->bs; i++) ans->org_q[i] = B_true->org_q[i];
  _ c2 = B2A(c, B_true->q);
  _ extended_c = extend_share_array(ans->bs, c2);
  ans->B = IfThenElse_channel(extended_c, B_true->B, B_false->B, 0);
  _free(extended_c);
  _free(c2);
  return ans;
}

#if 0
///////////////////////////////////////////////////////////////////////////////
// bits を block に変換してからオンラインで計算
///////////////////////////////////////////////////////////////////////////////
static _bits AppPerm_bits4_channel(_bits x, _ sigma, int inverse, int channel)
{
  if (_party >  2) return NULL;
  dshare ds;
  int d = x->d;
//  printf("AppPerm sigma:"); share_print(sigma);
//  printf("AppPerm x:"); share_print(x);
//  printf("sigma k=%d\n", sigma->A->w);
//  printf("x k=%d\n", x->A->w);
  int n = len(x->a[0]);
  if (n != len(sigma)) {
    printf("AppPerm: len(x) = %d len(sigma) = %d", len(x->a[0]), len(sigma));
  }
  perm g;
  if (_party == 0) {
  //  g = perm_random(n);
    g = perm_random(mt0, n);
  } else {
    g = perm_id(n);
  }
//  printf("g "); perm_print(g);

  ds = dshare_new_channel(g, order(sigma), channel);
  _ rho = dshare_shuffle_channel(sigma, ds, channel);
  dshare_free(ds);


  _ z;
  //NEWT(_bits, z);
  //NEWA(z->a, _, d);
  //z->d = d;
  _ w;
  //NEWT(_bits, w);
  //NEWA(w->a, _, d);
  //w->d = d;

  _ xb = Bits_to_block(x);


  if (inverse) {
#if 0
    dshare ds_x = dshare_new2_channel(g, order(x->a[0]), channel);
    for (int i=0; i<d; i++) {
      dshare_correlated_random_channel(ds_x, channel);
      z->a[i] = dshare_shuffle_channel(x->a[i], ds_x, channel);
      dshare_free3(ds_x);
    }
    dshare_free2(ds_x);
#else
    dshare ds_x = block_dshare_new_channel(d, g, order(xb), channel);
    z = block_dshare_shuffle_channel(d, xb, ds_x, channel);
    dshare_free(ds_x);
#endif
//    printf("AppInvPerm z:"); share_print(z);
  } else {
    if (_party <= 0) {
    //  printf("rho k=%d\n", rho->A->w);
    //  w = share_perm_bits(x, share_raw(rho));
#if 0
      for (int i=0; i<d; i++) {
        w->a[i] = share_perm(x->a[i], share_raw(rho));
      }
#else
    w = block_share_perm(d, xb, share_raw(rho));
#endif
    } else {
      _ r = _reconstruct_channel(rho, channel);
      //_save(r, "tmp_r");
      //w = share_perm_bits(x, share_raw(r));
#if 0
      for (int i=0; i<d; i++) {
        w->a[i] = share_perm(x->a[i], share_raw(r));
      }
#else
      w = block_share_perm(d, xb, share_raw(r));
#endif
      _free(r);
    }
//    printf("AppPerm w:"); share_print(w);
  }


  _bits ans;
  //NEWT(_bits, ans);
  //NEWA(ans->a, _, d);
  //ans->d = d;
  if (inverse == 0) {
    perm g_inv = perm_inverse(g);
//    printf("g_inv "); perm_print(g_inv);
//    ds = dshare_new_channel(g_inv, order(w), channel);
    ds = block_dshare_new_channel(d, g_inv, order(w), channel);

    //ans = dshare_shuffle_bits(w, ds);
#if 0
    for (int i=0; i<d; i++) {
      dshare_correlated_random_channel(ds, channel);
      ans->a[i] = dshare_shuffle_channel(w->a[i], ds, channel);
      dshare_free3(ds);
    }
#else
    _ ans_b = block_dshare_shuffle_channel(d, w, ds, channel);
    ans = block_to_Bits(d, ans_b);
    _free(ans_b);
#endif
    dshare_free(ds);
//    printf("AppPerm w2:"); share_print(w2);

    perm_free(g_inv);

  } else {
    _ r = _reconstruct_channel(rho, channel);
    perm rho_inv = perm_inverse(share_raw(r));
    //ans = share_perm_bits(z, rho_inv);
#if 0
    for (int i=0; i<d; i++) {
      ans->a[i] = share_perm(z->a[i], rho_inv);
    }
#else
    _ ans_b = block_share_perm(d, z, rho_inv);
    ans = block_to_Bits(d, ans_b);
    _free(ans_b);
#endif
    _free(r);
    //_free(z);
    //_free_bits(z);
    perm_free(rho_inv);
  }

  perm_free(g);
  _free(rho);
  if (inverse == 0) _free(w);
//  if (inverse == 0) _free_bits(w);
  _free(xb);
  _free(z);

  return ans;
}
#define AppPerm_bits4(a, sigma) AppPerm_bits4_channel(a, sigma, 0, 0)
#define AppInvPerm_bits4(a, sigma) AppPerm_bits4_channel(a, sigma, 1, 0)
#endif

static _bits block_AppPerm_bits_bd_channel(int bs, _bits x, _ sigma, int inverse, int channel) {
  int d = x->d;
  if (len(x->a[0]) / bs != len(sigma)) {
    printf("block_AppPerm_bits_bd_channel len(x->a[0]) / bs = %d, len(sigma) = %d\n", len(x->a[0]) / bs, len(sigma));
    exit(1);
  }
  _ xb = Bits_to_block(x);
  _ ans_b;
  if (inverse) {
    ans_b = block_AppPerm_inverse_channel(d * bs, xb, sigma, channel);
  }
  else {
    ans_b = block_AppPerm_fwd_channel(d * bs, xb, sigma, channel);
  }
  _bits ans = block_to_Bits(d, ans_b);
  _free(ans_b);
  _free(xb);

  return ans;
}
#define block_AppPerm_bits_channel(bs, a, sigma, channel) block_AppPerm_bits_bd_channel(bs, a, sigma, 0, channel)
#define block_AppInvPerm_bits_channel(bs, a, sigma, channel)  block_AppPerm_bits_bd_channel(bs, a, sigma, 1, channel)
#define block_AppPerm_bits(bs, a, sigma)  block_AppPerm_bits_bd_channel(bs, a, sigma, 0, 0)
#define block_AppInvPerm_bits(bs, a, sigma) block_AppPerm_bits_bd_channel(bs, a, sigma, 1, 0)

static void block_AppPerm_bits_bd_channel_(int bs, _bits x, _ sigma, int inverse, int channel) {
  _bits res = block_AppPerm_bits_bd_channel(bs, x, sigma, inverse, channel);
//  _free_bits(x);
//  x = res;
  _move_bits(x, res);
}
#define block_AppPerm_bits_channel_(bs, a, sigma, channel) block_AppPerm_bits_bd_channel_(bs, a, sigma, 0, channel)
#define block_AppInvPerm_bits_channel_(bs, a, sigma, channel)  block_AppPerm_bits_bd_channel_(bs, a, sigma, 1, channel)
#define block_AppPerm_bits_(bs, a, sigma)  block_AppPerm_bits_bd_channel_(bs, a, sigma, 0, 0)
#define block_AppInvPerm_bits_(bs, a, sigma) block_AppPerm_bits_bd_channel_(bs, a, sigma, 1, 0)


static _bits AppPerm_bits_bd_channel(_bits x, _ sigma, int inverse, int channel)
{
  int d = x->d;
  _ xb = Bits_to_block(x);
  _ ans_b;
  if (inverse) {
    ans_b = block_AppPerm_inverse_channel(d, xb, sigma, channel);
  } else {
    ans_b = block_AppPerm_fwd_channel(d, xb, sigma, channel);
  }
  _bits ans = block_to_Bits(d, ans_b);
  _free(ans_b);
  _free(xb);

  return ans;
}
//#define AppPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 0, 0) // !!!!!
#define AppPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 0, channel)
//#define AppInvPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 1, 0) // !!!!!
#define AppInvPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 1, channel)
#define AppPerm_bits(a, sigma) AppPerm_bits_channel(a, sigma, 0)
#define AppInvPerm_bits(a, sigma) AppInvPerm_bits_channel(a, sigma, 0)

#if 0
// 通信量が多い
static _bits AppPerm_new_bits3_channel(_bits x, _ sigma, int inverse, int channel)
{
  if (_party >  2) return NULL;
  int d = x->d;

  NEWT(_bits, ans);
  NEWA(ans->a, _, d);
  ans->d = d;

  for (int i=0; i<d; i++) {
    if (inverse) {
      ans->a[i] = block_AppPerm_inverse_channel(1, x->a[i], sigma, channel);
    } else {
      ans->a[i] = block_AppPerm_fwd_channel(1, x->a[i], sigma, channel);
    }
  }

  return ans;
}

static _bits AppInvPerm_bits3_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  return AppPerm_new_bits3_channel(a, sigma, 1, channel);
}
#define AppInvPerm_bits3(a, sigma) AppInvPerm_bits3_channel(a, sigma, 0)

static _bits AppPerm_bits3_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  return AppPerm_new_bits3_channel(a, sigma, 0, channel);
}
#define AppPerm_bits3(a, sigma) AppPerm_bits3_channel(a, sigma, 0)
#endif


#if 0
static _ AppPerm_channel(_ x, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  //_ ans = AppPerm_new_channel(x, sigma, 0, channel);
  _ ans = AppPerm_fwd_channel(x, sigma, channel);
  return ans;
}
#endif

static _ AppPerm_channel(_ x, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  //_ ans = AppPerm_new_channel(x, sigma, 0, channel);
  _ ans = block_AppPerm_fwd_channel(1, x, sigma, channel);
  return ans;
}

static _ AppPerm(_ x, _ sigma)
{
  //if (_party >  2) return NULL;
  return AppPerm_fwd_channel(x, sigma, 0);
}

static void AppPerm_channel_(_ x, _ sigma, int channel)
{
  //if (_party >  2) return;
//  _ ans = AppPerm_new_channel(x, sigma, 0, channel);
  _ ans = AppPerm_fwd_channel(x, sigma, channel);
  _move_(x, ans);
}
#define AppPerm_(x, sigma) AppPerm_channel_(x, sigma, 0)

#if 0
static _ AppInvPerm_channel(_ x, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  //_ ans = AppPerm_new_channel(x, sigma, 1, channel);
  _ ans = AppPerm_inverse_channel(x, sigma, channel);
  return ans;
}
#define AppInvPerm_(x, sigma) AppInvPerm_channel_(x, sigma, 0)
#endif

static _ AppInvPerm_channel(_ x, _ sigma, int channel)
{
  //if (_party >  2) return NULL;
  _ ans = block_AppPerm_inverse_channel(1, x, sigma, channel);
  return ans;
}
#define AppInvPerm(x, sigma) AppInvPerm_channel(x, sigma, 0)


static void AppInvPerm_channel_(_ x, _ sigma, int channel)
{
  //if (_party >  2) return;
//  _ ans = AppPerm_new_channel(x, sigma, 1, channel);
  _ ans = AppPerm_inverse_channel(x, sigma, channel);
  _move_(x, ans);
}
#define AppInvPerm_(x, sigma) AppInvPerm_channel_(x, sigma, 0)

// static share_array* Parallel_block_AppInvPerm_inverse_channel(int bs, int m, share_array *x, share_array *sigma, int channel) {
//   if (_party > 2) return NULL;
//   int n = len(x) / bs;
//   if (n != len(sigma)) {
//     printf("Parallel_block_AppInvPerm_channel: block_len(x) %d len(sigma) %d\n", n, len(sigma));
//   }

//   dshare
// }

#if 0
static void AppInvPerm_bits_channel_(_bits a, _ sigma, int channel)
{
  if (_party >  2) return;
  for (int i=0; i<a->d; i++) {
    AppInvPerm_channel_(a->a[i], sigma, channel);
  }
}
#define AppInvPerm_bits_(a, sigma) AppInvPerm_bits_channel_(a, sigma, 0)

static void AppPerm_bits_channel_(_bits a, _ sigma, int channel)
{
  if (_party >  2) return;
  for (int i=0; i<a->d; i++) {
    AppPerm_channel_(a->a[i], sigma, channel);
  }
}
#define AppPerm_bits_(a, sigma) AppPerm_bits_channel_(a, sigma, 0)
#endif

#if 0
static _bits AppInvPerm_bits_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);
  NEWA(ans->a, _, a->d);
  ans->d = a->d;
  for (int i=0; i<a->d; i++) {
    ans->a[i] = AppInvPerm_channel(a->a[i], sigma, channel);
  }
  return ans;
}
#define AppInvPerm_bits(a, sigma) AppInvPerm_bits_channel(a, sigma, 0)


static _bits AppPerm_bits_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);
  NEWA(ans->a, _, a->d);
  ans->d = a->d;
  for (int i=0; i<a->d; i++) {
    ans->a[i] = AppPerm_channel(a->a[i], sigma, channel);
  }
  return ans;
}
#define AppPerm_bits(a, sigma) AppPerm_bits_channel(a, sigma, 0)
#endif

static _bits AppPerm_bits_online_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  return AppPerm_new_bits_channel(a, sigma, 0, channel);
}
#define AppPerm_bits_online(a, sigma) AppPerm_bits_online_channel(a, sigma, 0)

static _bits AppInvPerm_bits_online_channel(_bits a, _ sigma, int channel)
{
  if (_party >  2) return NULL;
  return AppPerm_new_bits_channel(a, sigma, 1, channel);
}
#define AppInvPerm_bits_online(a, sigma) AppInvPerm_bits_online_channel(a, sigma, 0)


#if 0
typedef struct AppPerm_args {
  int channel; // 0, 1, ..., NC-1
  _ x;
  _ sigma;
  int inverse;
  _ ans;
}* AppPerm_args;

void *AppPerm_concurrent(void *args_) {
  if (_party >  2) return NULL;
  AppPerm_args args = (AppPerm_args)args_;
  int channel = args->channel;
  _ x = args->x;
  _ sigma = args->sigma;
  int inverse = args->inverse;
  _ ans;
  if (inverse == 0) {
    ans = AppPerm_fwd_channel(x, sigma, channel);
  } else {
    ans = AppPerm_inverse_channel(x, sigma, channel);
  }
  args->ans = ans;
  return NULL;
}

void *AppPerm_concurrent_(void *args_) {
  if (_party >  2) return NULL;
  AppPerm_concurrent(args_);
  AppPerm_args args = (AppPerm_args)args_;
  _move_(args->x, args->ans);
  return NULL;
}
#endif

#endif