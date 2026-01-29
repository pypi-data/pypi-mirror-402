#ifndef _COMPARE_H
 #define _COMPARE_H

//#include "share.h"
#include "func.h"
#include "field.h"

#ifndef max
 #define max(x, y) ((x > y)?x:y)
#endif

void _print_bits(_bits a)
{
//  if (_party >  2) return;
  for (int i=0; i<a->d; i++) {
    printf("i = %d ", i); _print(a->a[i]);
  }
}

void _free_bits(_bits a)
{
//  if (_party >  2) return;
  for (int i=0; i<a->d; i++){
    _free(a->a[i]);
  }
  free(a->a);
  free(a);
}

_bits _dup_bits(_bits a)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);
  ans->d = a->d;
  NEWA(ans->a, _, a->d); 
  for (int i=0; i<a->d; i++) {
    ans->a[i] = _dup(a->a[i]);
  }
  return ans;
}

_bits _vconcat_bits(_bits low, _bits high)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);
  ans->d = low->d + high->d;
  NEWA(ans->a, _, ans->d); 
  for (int i=0; i<low->d; i++) {
    ans->a[i] = _dup(low->a[i]);
  }
  for (int i=0; i<high->d; i++) {
    ans->a[low->d + i] = _dup(high->a[i]);
  }
  return ans;
}

_bits _concat_bits(_bits first, _bits second)
{
  if (_party >  2) return NULL;
  int d = first->d;
  if (d != second->d) {
    printf("concat_bits: depth %d %d\n", d, second->d);
    exit(1);
  }
  NEWT(_bits, ans);
  ans->d = d;
  NEWA(ans->a, _, d); 
  for (int i=0; i<d; i++) {
    ans->a[i] = _concat(first->a[i], second->a[i]);
  }
  return ans;
}

////////////////////////////////////////////////////////
// ビットのシェアを位数 q に変換
////////////////////////////////////////////////////////
_ B2A_online_channel(_b a, share_t q, int channel)
{
  if (_party >  2) return NULL;
  if (_opt.warn_precomp) {
    printf("without B2A_table\n"); fflush(stdout);
  }
  share_t r;
  if (a->q != 2) {
    printf("B2A: q = %d\n", a->q);
    exit(1);
  }
  int n = a->n;
  _ ans = _const(n, 0, q);
  //unsigned long init[5]={0x123, 0x234, 0x345, 0x456, 0};
  if (_party <= 0) {
    // c1 の生成
    _ c1 = _const(n, 0, 2);
    for (int i=0; i<n; i++) {
      share_t r;
    //  r = RANDOM(m0, 2);
      r = RANDOM(mt_[TO_PARTY1][channel], 2);
      pa_set(c1->A, i, r);
      //if (i == 0) printf("(r %d\n)", r);
    }

    // c2 の生成
    _ c2 = _const(n, 0, 2);
    for (int i=0; i<n; i++) {
    //  r = RANDOM(m0, 2);
      r = RANDOM(mt_[TO_PARTY2][channel], 2);
      pa_set(c2->A, i, r);
      //if (i == 0) printf("[r %d\n]", r);
    }
    _ c = _const(n, 0, 2);
    for (int i=0; i<n; i++) {
      pa_set(c->A, i, (pa_get(c1->A, i) + pa_get(c2->A, i)) % 2);
    }

    //init[4] = 0; // rand();
    _ f = _const(n, 0, q);
    //init_by_array(init, 5);
    for (int i=0; i<n; i++) {
      r = RANDOM(mt_[TO_PARTY2][channel], q);
      pa_set(f->A, i, MOD(r + pa_get(c->A, i)));
    }
    //mpc_send_channel(TO_PARTY1, f->A->B, pa_size(f->A), channel);
    mpc_send_share_channel(TO_PARTY1, f, channel);

    _free(c1);
    _free(c2);
    _free(c);
    _free(f);

    for (int i=0; i<n; i++) {
      pa_set(ans->A, i, pa_get(a->A, i));
    }
  } else {
    _ c = _const(n, 0, 2);
    for (int i=0; i<n; i++) {
      r = RANDOM(mt_[FROM_SERVER][channel], 2);
      //if (i == 0) printf("[r %d\n]", r);
      pa_set(c->A, i, r);
    }

    _ f0 = _const(n, 0, q);
    _ f1 = _const(n, 0, q);

  //  init_by_array(init, 5);
    if (_party == 1) {
      mpc_recv_channel(FROM_SERVER, f0->A->B, pa_size(f0->A), channel);
      for (int i=0; i<n; i++) {
        pa_set(f1->A, i, MOD(q+1 - pa_get(f0->A, i)));
      }
    } else { // party 2
      for (int i=0; i<n; i++) {
        r = RANDOM(mt_[FROM_SERVER][channel], q);
        pa_set(f0->A, i, MOD(q-r));
        pa_set(f1->A, i, MOD(r));
      }
    }
  //  printf("f0 "); _print(f0);
  //  printf("f1 "); _print(f1);
  //  printf("a  "); _print(a);
    _ b = vsub(a, c);
    _ b_c = _reconstruct_channel(b, channel);
  //  printf("b  "); _print(b);
  //  printf("bc "); _print(b_c);
//    share_t x;
    for (int i=0; i<n; i++) {
      if (pa_get(b_c->A, i) == 0) {
        pa_set(ans->A, i, MOD(pa_get(f0->A, i)));
      } else {
        pa_set(ans->A, i, MOD(pa_get(f1->A, i)));
      }
    }
    _free(f0);
    _free(f1);
    _free(b);
    _free(b_c);
    _free(c);
  //  printf("ans "); _print(ans);
  }
  return ans;
}



_ overflow1_online_channel(_b a, share_t q, int channel)
{
  if (_party >  2) {
    return NULL;
  }
  int n = len(a);

  _ b1 = _const(n, 0, q);
  if (_party == 2) {
    for (int i=0; i<n; i++) {
      pa_set(b1->A, i, (q+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット
    }
  }
  _ b2 = _const(n, 0, q);
  if (_party != 2) {
    for (int i=0; i<n; i++) {
      pa_set(b2->A, i, (q+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット
    }
  }
  _ ans = vmul_channel(b1, b2, channel);

  _free(b1); _free(b2);
  return ans;
}



//#define B2A(a, q) B2A_online_channel(a, q, 0)
_ B2A_channel(_b a, share_t q, int channel)
{
  if (_party > 2) return NULL; // 要検討
  int n = len(a);

  if (_party == -1) {
    _ ans = _const(n, 0, q);
    //pa_iter itr_ans = pa_iter_new(ans->A);
    //pa_iter itr_a = pa_iter_new(a->A);
    NEWITER(itr_ans, ans);
    NEWITER(itr_a, a);
    for (int i=0; i<n; i++) {
      //pa_set(ans->A, i, pa_get(a->A, i));
      pa_iter_set(itr_ans, pa_iter_get(itr_a));
    }
    pa_iter_flush(itr_ans);
    pa_iter_free(itr_a);
    return ans;
  }

  _ tmp = NULL;
  if (PRE_B2A_tbl[channel] != NULL) {
    PRE_B2A_count[channel] += len(a);
    return func1bit_channel(a, q, PRE_B2A_tbl[channel], channel);
  //  tmp = func1bit_channel(a, q, PRE_B2A_tbl[channel], channel);
  }

  if (PRE_OF_tbl[1-1][channel] != NULL) {
    _ ans = _const(n, 0, q);
    NEWITER(itr_ans, ans);
    NEWITER(itr_a, a);
    for (int i=0; i<n; i++) {
      //pa_set(ans->A, i, pa_get(a->A, i));
      pa_iter_set(itr_ans, pa_iter_get(itr_a));
    }
    pa_iter_flush(itr_ans);
    pa_iter_free(itr_a);
    _ bo = overflow_channel(1, a, q, channel);
    smul_(2, bo);
    vsub_(ans, bo);
    _free(bo);
    return ans;
  }
//  printf("B2A ans "); _print(ans);
//  if (tmp) {printf("B2A tmp "); _print(tmp);}

//  _check(tmp);

//  return tmp;
  return B2A_online_channel(a, q, channel);
}
#define B2A(a, q) B2A_channel(a, q, 0)

static void B2A_channel_(_b a, share_t q, int channel) {
  if (_party > 2) return;
  _ ans = B2A_channel(a, q, channel);
  _move_(a, ans);
} 

static void B2A_(_b a, share_t q)
{
  if (_party >  2) return;
  _ ans = B2A(a, q);
  _move_(a, ans);
}



////////////////////////////////////////////////////////
// 加法的シェアを最下位ビットのシェアとそれ以外のシェアに変換する
// 位数 q は2のべき乗とする
// それ以外のシェアの位数は q/2 となる
// 最下位ビットのシェアの位数は qb になる
////////////////////////////////////////////////////////
_pair share_A2QB_channel(_ a, share_t q, share_t qb, int channel)
{
  if (_party >  2) {
    _pair ans = {NULL, NULL};
    return ans;
  }
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2QB: %d is not a power of two\n", (int)q);
  }

  int n = len(a);
  //printf("share_A2QB q = %d qb = %d\n", q, qb);
  _ b = _const(n, 0, qb);
  for (int i=0; i<n; i++) {
    pa_set(b->A, i, (q+pa_get(a->A,i)) % 2); // 加法的シェアの最下位ビット
  }
  _ b1 = _const(n, 0, qb);
  if (_party == 2) {
    for (int i=0; i<n; i++) {
      pa_set(b1->A, i, (q+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット
    }
  }
  _ b2 = _const(n, 0, qb);
  if (_party != 2) {
    for (int i=0; i<n; i++) {
      pa_set(b2->A, i, (q+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット
    }
  }
  _ bp = vmul_channel(b1, b2, channel);
  //printf("b  "); _print(b);
  //printf("b1 "); _print(b1);
  //printf("b2 "); _print(b2);
  //printf("bp "); _print(bp);
  for (int i=0; i<n; i++) {
    pa_set(b->A, i, (10*qb + pa_get(b->A, i) - 2*pa_get(bp->A, i)) % qb); // b のシェアが両方 1 だと本来は 0 なのに 2 になってしまう
  }


  q = q/2;
  _ x;
  if (q > 1) {

    _ c1 = _const(n, 0, q);
    if (_party == 2) {
      for (int i=0; i<n; i++) {
        pa_set(c1->A, i, (q*4+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット !!!
      }
    }
    _ c2 = _const(n, 0, q);
    if (_party != 2) {
      for (int i=0; i<n; i++) {
        pa_set(c2->A, i, (q*4+pa_get(a->A, i)) % 2); // 加法的シェアの最下位ビット
      }
    }
    _ c = vmul_channel(c1, c2, channel);


    x = _const(n, 0, q);

    for (int i=0; i<n; i++) {
      pa_set(x->A, i, ((q*4+pa_get(a->A, i)) / 2) % q); // !!!
    }
    vadd_(x, c);

    _free(c1); _free(c2); _free(c);
  } else {
    x = _const(n, 0, 2);
  }

  _pair ans = {x, b};
  _free(b1); _free(b2); _free(bp);


  return ans;
}
#define _A2QB share_A2QB

_pair share_A2QB_xor(_ a)
{
  share_t q = order(a);
  if (_party >  2) {
    _pair ans = {NULL, NULL};
    return ans;
  }
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2QB_xor: %d is not a power of two\n", (int)q);
  }

  int n = len(a);
  _ b = _const(n, 0, 2);
  for (int i=0; i<n; i++) {
    pa_set(b->A, i, (q+pa_get(a->A,i)) % 2); // xor シェアの最下位ビット
  }


  q = q/2;
  _ x;
  if (q > 1) {
    x = _const(n, 0, q);
    for (int i=0; i<n; i++) {
      pa_set(x->A, i, ((q*4+pa_get(a->A, i)) / 2) % q); // !!!
    }
  } else {
    x = _const(n, 0, 2);
  }

  _pair ans = {x, b};

  return ans;
}

#define share_A2QB(a, q, qb) share_A2QB_channel(a, q, qb, 0)

_pair share_A2QB3_channel(precomp_tables T, _ a, share_t q, share_t qb, int channel)
{
  if (_party >  2) {
    _pair ans = {NULL, NULL};
    return ans;
  }
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2QB3: %d is not a power of two\n", (int)q);
  }

  share_t q3 = max(q/2, qb);


  int n = len(a);
//  printf("share_A2QB q = %d qb = %d\n", q, qb);
  _ b = _const(n, 0, qb);
  _ bb = _const(n, 0, 2);
  for (int i=0; i<n; i++) {
    //pa_set(b->A, i, (q+pa_get(a->A,i)) % 2); // 加法的シェアの最下位ビット
    //pa_set(bb->A, i, (q+pa_get(a->A,i)) % 2); // 加法的シェアの最下位ビット
    share_t z = (q+pa_get(a->A,i)) % 2; // 加法的シェアの最下位ビット
    pa_set(b->A, i, z);
    pa_set(bb->A, i, z);
  }

//  share_t table_overflow[] = {0, 0, 0, 1};
//  printf("\nbb "); _print(bb);
//  _ bo = func1bit2(bb, qb, table_overflow);
//  _ bo = func1bit2(bb, q3, table_overflow);
  _ bo = func1bit3_channel(bb, q3, T, channel);
//  printf("\nbo "); _print(bo);

  for (int i=0; i<n; i++) {
    //printf("b[i] = %d bo[i] = %d %d \n", pa_get(b->A, i), pa_get(bo->A, i), (10*qb + pa_get(b->A, i) - 2*pa_get(bo->A, i)));
    //pa_set(b->A, i, (10*qb + pa_get(b->A, i) - 2*pa_get(bo->A, i)) % qb); // b のシェアが両方 1 だと本来は 0 なのに 2 になってしまう
    pa_set(b->A, i, (2*qb + pa_get(b->A, i) - 2*(pa_get(bo->A, i)%qb)) % qb); // b のシェアが両方 1 だと本来は 0 なのに 2 になってしまう
  }


  q = q/2;
  _ x;
  if (q > 1) {
    x = _const(n, 0, q);
#if 0
    for (int i=0; i<n; i++) {
      pa_set(x->A, i, ((q*4+pa_get(a->A, i)) / 2) % q); // !!!
    }
    for (int i=0; i<n; i++) {
      pa_set(x->A, i, (10*q + pa_get(x->A, i) + pa_get(bo->A, i)) % q);
    }
#else
    for (int i=0; i<n; i++) {
      share_t z;
      z = (q*4+pa_get(a->A, i)) / 2;
      z += pa_get(bo->A, i);
      pa_set(x->A, i, z % q);
    }
#endif
  } else {
    x = _const(n, 0, 2);
  }

  _pair ans = {x, b};

  _free(bb);  _free(bo);

  return ans;
}
#define share_A2QB3(T, a, q, qb) share_A2QB3_channel(T, a, q, qb, 0)

////////////////////////////////////////////////////////
// 加法的シェアを最下位ビットのシェアとそれ以外のシェアに変換する
// 位数 q は2のべき乗とする
// それ以外のシェアの位数は q/2 となる
// 最下位ビットのシェアの位数は qb になる
////////////////////////////////////////////////////////
_pair share_A2QB_channel2(_ a, share_t q, share_t qb, int channel)
{
  if (_party > 2) {
    _pair ans = {NULL, NULL};
    return ans;
  }

  _pair ans;

  if (PRE_OF_tbl[0][channel] != NULL) {
//test  if (_party >= 0 && PRE_OF_tbl[0][channel] != NULL) { // !!!
    //printf("share_A2QB_channel2 using tables\n");
    PRE_OF_count[0][channel] += len(a);
    ans = share_A2QB3_channel(PRE_OF_tbl[0][channel], a, q, qb, channel);
  } else {
    //printf("share_A2QB_channel2 no tables\n");
    ans = share_A2QB_channel(a, q, qb, channel);    
  }

  return ans;
}


///////////////////////////////////////////////////////////////////////////////
// 下位 d ビットとそれ以外に分ける
///////////////////////////////////////////////////////////////////////////////
_pair share_A2QD_channel(int d, _ a, share_t q, share_t qb, int channel)
{
  if (_party > 2) {
    NEWT(_, b);
    *b = *a;
    b->A = NULL;
    b->q = qb;
    NEWT(_, x);
    *x = *a;
    x->A = NULL;
    int w = 1 << d;
    q = q/w;
    if (q < 2) q = 2;
    x->q = q;
    _pair ans = {x, b};
    return ans;
  }
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2QD: %d is not a power of two\n", (int)q);
  }
  int w = 1 << d;
  //if (q < w) w = q; // test

//  printf("A2QD a "); _print(a);

  share_t q3 = max(q/w, qb);


  int n = len(a);
//  printf("share_A2QB q = %d qb = %d\n", q, qb);
  _ b = _const(n, 0, qb); // 下位桁
  _ bb = _const(n, 0, w); // 繰り上がりの計算用
  for (int i=0; i<n; i++) {
    pa_set(b->A, i, (q+pa_get(a->A,i)) % w); // 加法的シェアの下位 d ビット
    pa_set(bb->A, i, (q+pa_get(a->A,i)) % w); // 加法的シェアの下位 d ビットからの繰り上がりの計算で用いる
  }

//  printf("A2QD b  "); _print(b);
//  printf("A2QD bb "); _print(bb);

  _ bo = overflow_channel(d, bb, q3, channel);

  for (int i=0; i<n; i++) {
    //pa_set(b->A, i, (w*qb + pa_get(b->A, i) - w*pa_get(bo->A, i)) % qb); // b の位数を w から qb に拡張するときの補正
    pa_set(b->A, i, (w*qb + pa_get(b->A, i) - w*pa_get(bo->A, i)) & (qb-1)); // b の位数を w から qb に拡張するときの補正
  }
//  printf("hi "); _print(b);


  q = q/w; // 上位桁の位数
  _ x;
  if (q > 1) {
    x = _const(n, 0, q);

    for (int i=0; i<n; i++) {
    //  pa_set(x->A, i, ((q*4+pa_get(a->A, i)) / w) % q); // !!!
      pa_set(x->A, i, ((q*0+pa_get(a->A, i)) / w) % q); // !!!
    }
  //  printf("A2QD x1 "); _print(x);
    for (int i=0; i<n; i++) {
      pa_set(x->A, i, (4*q + pa_get(x->A, i) + pa_get(bo->A, i)) % q); // 下位桁からの繰り上がりを足す
    }
  } else {
    x = _const(n, 0, 2);
  }

//  printf("A2QD x2 "); _print(x);
//  printf("A2QD b  "); _print(b);

  _pair ans = {x, b};

  _free(bb);  _free(bo);

  return ans;
}



////////////////////////////////////////////////////////
// 加法的シェアをビットごとのシェア（位数 qb）に変換する
// 位数 q は2のべき乗とする
////////////////////////////////////////////////////////
_bits share_A2B(_ a, share_t qb)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);

  share_t q = order(a);
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2B: %d is not a power of two\n", (int)q);
  }
  ans->d = k;
//  int n = len(a);

  NEWA(ans->a, share_array, k);
  _ x = _dup(a);
  for (int i = 0; i<k; i++) {
    _pair tmp = share_A2QB(x, order(x), qb);
    ans->a[i] = tmp.y;
    _move_(x, tmp.x);
  }
  _free(x);

  return ans;
}
//#define _A2B share_A2B


_bits share_A2B_channel(_ a, share_t qb, int channel)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);

  share_t q = order(a);
  int k = blog(q-1)+1;
  if ((1 << k) != q) {
    printf("share_A2B: %d is not a power of two\n", (int)q);
  }
  ans->d = k;
//  int n = len(a);

  NEWA(ans->a, share_array, k);
  _ x = _dup(a);
  for (int i = 0; i<k; i++) {
    _pair tmp = share_A2QB_channel2(x, order(x), qb, channel);
    ans->a[i] = tmp.y;
    _move_(x, tmp.x);
  }
  _free(x);

  return ans;
}
#define _A2B(a, qb) share_A2B_channel(a, qb, 0)
#define _A2B_channel(a, qb, channel) share_A2B_channel(a, qb, channel)

////////////////////////////////////////////////////////
// 加法的シェア（位数 1<<k1）を位数 qb = 1<<k2 に変換する (k1 < k2)
////////////////////////////////////////////////////////
_ share_extend(_ a, share_t qb)
{
  if (_party >  2) return NULL;

  share_t q = order(a);
  if (qb < q) {
    printf("share_extend: q = %d qb = %d\n", (int)q, (int)qb);
  }
  int k1 = blog(q-1)+1;
  int k2 = blog(qb-1)+1;
  if ((1 << k1) != q) {
    printf("share_extend: %d is not a power of two\n", (int)q);
  }
  if ((1 << k2) != qb) {
    printf("share_extend: %d is not a power of two\n", (int)qb);
  }
  int n = len(a);
  _bits b = _A2B(a, qb);

  _ ans = _const(n, 0, qb);
  ans->type = SHARE_T_22ADD;

  for (int k=b->d-1; k>=0; k--) {
    smul_(2, ans);
    vadd_(ans, b->a[k]);
  }
  _randomize(ans); // 不要?

  _free_bits(b);

  return ans;
}
#define _extend share_extend

_ share_shrink(_ a, share_t q)
{
  if (_party >  2) return NULL;

  share_t qa = order(a);
  if (q > qa) {
    printf("share_shrink: qa = %d q = %d\n", (int)qa, (int)q);
  }
  int k1 = blog(qa-1)+1;
  int k2 = blog(q-1)+1;
  if ((1 << k1) != qa) {
    printf("share_shrink: %d is not a power of two\n", (int)qa);
  }
  if ((1 << k2) != q) {
    printf("share_shrink: %d is not a power of two\n", (int)q);
  }
  int n = len(a);

  _ ans = _const(n, 0, q);

  for (int i=0; i<n; i++) {
    pa_set(ans->A, i, MOD(pa_get(a->A, i)));
  }
//  _randomize(ans);

  return ans;
}
#define _shrink share_shrink


//////////////////////////////////////////////////////////////////////////
// 加法的シェア（位数 1<<k0）を k ビット左シフトし，位数 1<<(k0+k) に変換する
//////////////////////////////////////////////////////////////////////////
_ share_lshift_extend(_ a, int k)
{
  if (_party >  max_partyid(a)) return NULL;

  if (a->type != SHARE_T_22ADD && a->type != SHARE_T_33ADD && a->type != SHARE_T_RSS && a->type != SHARE_T_SHAMIR) {
    printf("share_lshift_extend: type = %d\n", a->type);
    exit(1);
  }
  if (a->irr_poly != 0) {
    printf("share_lshift_extend: irr_poly = %d\n", a->irr_poly);
    exit(1);
  }

  share_t q0 = order(a);
  int k0 = blog(q0-1)+1;
  if ((1 << k0) != q0) {
    printf("share_lshift_extend: %d is not a power of two\n", (int)q0);
  }
  share_t q = q0 << k;
  int n = len(a);

  _ ans = share_const_type(n, 0, q, a->type);
  *ans = *a;

  NEWITER(itr_a, a);
  NEWITER(itr_ans, ans);
  for (int i=0; i<n; i++) {
    share_t x = pa_iter_get(itr_a);
    pa_iter_set(itr_ans, x << k);
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a);

  //_randomize(ans); // 不要?

  return ans;
}
#define _extend share_extend



/////////////////////////////////////////////////
// ビット分解されている v に対し v[i] := x を行う
/////////////////////////////////////////////////
void _setpublic_bits(_bits v, int i, share_t x)
{
  if (_party >  2) return;
  for (int d=0; d<v->d; d++) {
    _setpublic(v->a[d], i, (x>>d) & 1);
  }
}

int len_bits(_bits b)
{
  return len(b->a[0]);
}

int order_bits(_bits b)
{
  return order(b->a[0]);
}

int depth_bits(_bits b)
{
  return b->d;
}

static _bits share_const_bits(int n, share_t v, share_t q, int d)
{
  if (_party >  2) return NULL;
  NEWT(_bits, ans);
  ans->d = d;
  NEWA(ans->a, _, d); 
  for (int i=0; i<d; i++) {
    ans->a[i] = _const(n, 0, q);
  }

  for (int i=0; i<n; i++) {
    _setpublic_bits(ans, i, v);
  }
  return ans;
}
#define _const_bits share_const_bits

static _bits share_const_bits_3party(int n, share_t v, share_t q, int d)
{
  if (_party >  3) return NULL;
  NEWT(_bits, ans);
  ans->d = d;
  NEWA(ans->a, _, d); 
  for (int i=0; i<d; i++) {
    ans->a[i] = share_const_type(n, 0, q, SHARE_T_SHAMIR);
  }

  for (int i=0; i<n; i++) {
    _setpublic_bits(ans, i, v);
  }
  return ans;
}
#define _const_bits_3party share_const_bits_3party

////////////////////////////////////////////
// a[i] := b[j]
////////////////////////////////////////////
static void share_setshare_bits(_bits a, int i, _bits b, int j)
{
  if (_party >  2) return;
  if (i < 0 || i >= a->a[0]->n) {
    printf("share_setshare_bits a: n %d i %d\n", a->a[0]->n, i);
    exit(1);
  }
  if (j < 0 || j >= b->a[0]->n) {
    printf("share_setshare_bits b: n %d j %d\n", b->a[0]->n, j);
    exit(1);
  }
  if (a->a[0]->q != b->a[0]->q) {
    printf("share_setshare_bits a->q %d b->q %d\n", (int)a->a[0]->q, (int)b->a[0]->q);
    exit(1);
  }
  if (a->d != b->d) {
    printf("share_setshare_bits a->d %d b->d %d\n", (int)a->d, (int)b->d);
    exit(1);
  }
  for (int k=0; k<a->d; k++) {
    pa_set(a->a[k]->A,i, pa_get(b->a[k]->A,j));
  }
}
#define _setshare_bits share_setshare_bits

static _bits share_slice_bits(_bits a, int start, int end)
{
  if (_party >  2) return NULL;
  if (start < 0) start = a->a[0]->n + start;
  if (end <= 0) end = a->a[0]->n + end;
  if (start < 0 || start > a->a[0]->n) {
    printf("share_slice_bits n %d start %d\n", a->a[0]->n, start);
  }
  if (end < 0 || end > a->a[0]->n) {
    printf("share_slice_bits n %d end %d\n", a->a[0]->n, end);
  }
  _bits ans = _const_bits(end-start, 0, a->a[0]->q, a->d);
  for (int i=0; i<ans->a[0]->n; i++) _setshare_bits(ans, i, a, start+i);
  return ans;
}
#define _slice_bits share_slice_bits

static share_t debug_get_bits(_bits a, int i)
{
  _bits tmp = share_slice_bits(a, i, i+1);
  //_bits tmp2 = share_reconstruct_bits_channel(tmp, 0);
  share_t ans = 0;
  for (int d = tmp->d-1; d >= 0; d--) {
    ans <<= 1;
    ans += debug_get(tmp->a[d], 0);
  }
  _free_bits(tmp);
  return ans;
}



//////////////////////////////////////////////////
// ビットごとのシェアから加法的シェアに変換
// 各桁のシェアの位数は元の位数と等しいと仮定
//（つまり繰り上がりはそのまま扱えば良い）
//////////////////////////////////////////////////
_ _B2A_bits(_bits b)
{
  if (_party >  2) return NULL;
  // 元の位数が 2 だとダメ
  if (b->a[0]->q == 2) {
    printf("B2A_bits: warning q = %d\n", b->a[0]->q);
  }
  _ ans = _const(b->a[0]->n, 0, b->a[0]->q);
//  printf("B2A: not supported yet\n");
//  exit(1);
  for (int k=b->d-1; k>=0; k--) {
    smul_(2, ans);
    vadd_(ans, b->a[k]);
  }
  return ans;
}

static _ B2A_GF(_bits x, share_t irr_poly)
{
  share_t q = 1 << x->d;
  int n = len(x->a[0]);
  //int n = x->a[0]->n;
  _ ans = share_const_type(n, 0, q, x->a[0]->type);
  ans->type = x->a[0]->type;
  ans->irr_poly = irr_poly;
  for (int i=0; i<ans->n; i++) {
    share_t z;
    z = 0;
    for (int j=x->d-1; j>=0; j--) {
    //  z <<= 1;
    //  z += share_getraw(x->a[j], i);
      share_t t = share_getraw(x->a[j], i);
      z ^= GF_mul(t, (1<<j), irr_poly);
    }
    share_setraw(ans, i, z);
  }
  return ans;
}



#define COMP_pPE 0
#define COMP_PIE 1
#define COMP_LT 2
#define COMP_LE 3
#define COMP_EQ 4
#define COMP_GE 5
#define COMP_GT 6
#define COMP_3 7



//////////////////////////////////////////////////////////////////
// comp_sub2
// input x, y
// output bi
// bi は長さ 2l+1 の配列
// bi[2l]   == 1 → x == y
// bi[2i]   == 1 → x < y  かつ i ビット目が異なる
// bi[2i+1] == 1 → x > y  かつ i ビット目が異なる
//////////////////////////////////////////////////////////////////
#if 0
int comp_sub2(Zp x, Zp y, int bi[MAXW*2+1])
{
// constant
  Zp Zp_1, Zp_3;
  int l;
  value_t p;
// shared
  value_t cyclic_shift;
// P1
  Zp xp[MAXW*2+1];
// P2
  Zp yp[MAXW*2+1];
// P3
//  int bi[MAXW*2+1];
  int bi_len;
// tmp
  int i;
//  Zp z;

// error check
  if (x.p != y.p) {
    printf("comp_sub2: x.p = %ld y.p = %ld\n", x.p, y.p);
    exit(1);
  }
   p = x.p;
   l = blog(p-1)+1;
   if (l > MAXW) {
    printf("comp_sub2: l = %d MAXW = %d\n", l, MAXW);
    exit(1);
   }

  printf("comp_sub2: x=%ld, y=%ld p=%ld\n", x.v, y.v, p);


// constant
  Zp_1 = Zp_new(1, p);
  Zp_3 = Zp_new(3, p);

// shared
  cyclic_shift = shared_random(l*2+1);
  cyclic_shift = 0;


// P1

  for (i=l-1; i>=0; i--) {
    Zp t, xb, xs;
    Zp x2;

    x2 = x;
    xs = Zp_new(x2.v >> i, p);        // x2 の i+1 ビット目から上の部分
    xb = Zp_new(Zp_getbit(x2, i), p); // x2 の下から i ビット目
    t = add_Zp(mul_Zp(xs, sub_Zp(Zp_1,xb)),xb);
    xp[(i*2 + cyclic_shift) % (l*2+1)] = t;

    x2 = x;
    x2.v = x2.v ^ ((1<<l)-1); // r==1 なら反転
    xs = Zp_new(x2.v >> i, p);
    xb = Zp_new(Zp_getbit(x2, i), p);
    t = add_Zp(mul_Zp(xs, sub_Zp(Zp_1,xb)),xb);
    xp[(i*2+1 + cyclic_shift) % (l*2+1)] = t;
  }

  xp[(l*2 + cyclic_shift) % (l*2+1)] = x;

// P2
  for (i=l-1; i>=0; i--) {
    Zp t, yb, ys;
    Zp y2;

    y2 = y;
    ys = Zp_new(y2.v >> i, p);
    yb = Zp_new(Zp_getbit(y2, i), p);
    t = add_Zp(mul_Zp(sub_Zp(ys, Zp_1), yb), mul_Zp(Zp_3, sub_Zp(Zp_1, yb)));
    yp[(i*2 + cyclic_shift) % (l*2+1)] = t;

    y2 = y;
    y2.v = y2.v ^ ((1<<l)-1);
    ys = Zp_new(y2.v >> i, p);
    yb = Zp_new(Zp_getbit(y2, i), p);
    t = add_Zp(mul_Zp(sub_Zp(ys, Zp_1), yb), mul_Zp(Zp_3, sub_Zp(Zp_1, yb)));
    yp[(i*2+1 + cyclic_shift) % (l*2+1)] = t;
  }

  yp[(l*2 + cyclic_shift) % (l*2+1)] = y;

// P3
  bi_len = l*2+1;
  for (i=bi_len-1; i>=0; i--) {
    bi[(i + (l*2+1) - cyclic_shift) % (l*2+1)] = pPE(xp[i], yp[i]);
    printf("comp_sub2: i=%d bi=%d\n", i, bi[i]);
  }

  return bi_len;
}

///////////////////////////////////
// b = (x < y)
// bi は長さ 2l+1 の配列
// bi[2l]   == 1 → x == y
// bi[2i]   == 1 → x < y  かつ i ビット目が異なる
// bi[2i+1] == 1 → x > y  かつ i ビット目が異なる
// p must be a prime
///////////////////////////////////
int Comp(Zp x, Zp y, int mode)
{
  int i, bi_len;
  int bi[MAXW*2+1];

  bi_len = comp_sub2(x, y, bi);

  switch (mode) {
    case COMP_EQ:
      return (bi[bi_len-1] == 1);
    case COMP_LE:
      if (bi[bi_len-1] == 1) return 1;
    case COMP_LT:
      for (i = 0; i < bi_len-1; i += 2) {
        if (bi[i] == 1) return 1;
      }
      return 0;
    case COMP_GE:
      if (bi[bi_len-1] == 1) return 1;
    case COMP_GT:
      for (i = 1; i < bi_len-1; i += 2) {
        if (bi[i] == 1) return 1;
      }
      return 0;
    case COMP_3:
      if (bi[bi_len-1] == 1) return 0;
      for (i = 0; i < bi_len-1; i += 2) {
        if (bi[i  ] == 1) return -1;
        if (bi[i+1] == 1) return  1;
      }
    default:
      printf("Comp: mode=%d\n", mode);
      exit(1);
  }


#if 0
// debug
  if ((x.v < y.v) != b) {
    printf("PIE2:error x = %ld y = %ld b = %d\n", x.v, y.v, b);
    exit(1);
  }
#endif

  return -2; // unreachable
}
#endif

//////////////////////////////////////////////////////////////
// x[i] == y[i] のとき b[i] := 1
// x, y は mod 2^k, b は mod 2
//////////////////////////////////////////////////////////////
_b Equality_bit(_ x, _ y)
{
  //if (_party >  2) return NULL; // 要検討
  //if (order(x) != 2 || order(y) != 2) {
  //  printf("Equality_bit: x->q = %d y->q = %d\n", (int)x->q, (int)y->q);
  //}
//  int q = order(x);
//  printf("Equality x "); _print(x);
//  printf("Equality y "); _print(y);
  int q = 2;
  int n = len(x);
//  _ ans = _dup(x);
  _b ans = _const(n, 0, q);
  if (_party <= 1) {
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i, MOD(pa_get(x->A, i) + pa_get(y->A, i) + 1));
    }
  }
  if (_party == 2) {
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i, MOD(pa_get(x->A, i) + pa_get(y->A, i)));
    }
  }
//  printf("Equality ans "); _print(ans);
  return ans;
}


_ Equality2(_ a, _ b)
{
  if (a == NULL || b == NULL) {
    printf("Equality2: a = %p b = %p\n", a, b);
    return NULL;
  }
  if (a->q != 2 || b->q != 2) {
    printf("Equality2: a->q = %d b->q = %d\n", a->q, b->q);
  }
  //if (_party >  2) return NULL;
  _ ans = XOR(a, b);
  vneg_(ans);
  return ans;
}


_b Equality_bits(_bits x, _bits y)
{
  if (_party >  2) return NULL;
  if (x->d != y->d) {
    printf("Equality_bits: x->d = %d y->d = %d\n", x->d, y->d);
  }
  int d = x->d;
  _b b = Equality_bit(x->a[0], y->a[0]);
  vneg_(b);
  for (int i=1; i<d; i++) {
    _b c = Equality_bit(x->a[i], y->a[i]);
    vneg_(c);
    _move_(b, OR(b, c));
    _free(c);
  }
  vneg_(b);
  return b;
}

#if 0
_b Equality(_ x, _ y)
{
  if (_party >  2) return NULL;
  _bits bx, by;
  bx = _A2B(x, 2);
  by = _A2B(y, 2);
  _b c = Equality_bits(bx, by);
  _free_bits(bx);
  _free_bits(by);
  return c;
}
#endif
_b Equality(_ a, _ b)
{
  if (a == NULL || b == NULL) {
    printf("Equality: a = %p b = %p\n", a, b);
    return NULL;
  }
  //if (_party >  2) return NULL;
  int n = len(a);
  _ ans;
  if (_party > max_partyid(a)) {
    NEWA(ans, struct share_array, 1);
    *ans = *a;
    ans->q = 2;
    ans->type = SHARE_T_22ADD; // 要検討 BINARY?
    ans->A = NULL;
    return ans;
  }
  //printf("Equality3:\n");
  //printf("a "); _print(a);
  //printf("b "); _print(b);
  if (_party >= 0) {
    share_t q = order(a);
    int k = blog(q-1)+1; // 桁数
    _ c = _const(n*k, 0, 2);
    _ v;
    if (_party == 1) {
      v = vsub(a, b);
    } else {
      v = vsub(b, a);
    }
    //printf("v "); _print(v);

    int d = (_party & 1) ^ 1;
    for (int i=0; i<n; i++) {
      share_t x = pa_get(v->A, i);
      for (int j=0; j<k; j++) {
        pa_set(c->A, j*n+i, (x & 1) ^ d);
        x >>= 1;
      }
    }
    //printf("c "); _print(c);
    ans = AND_rec(c, n);
    _free(c); _free(v);
    if (_party == 0) _free(ans);
  }
  if (_party <= 0) {
    ans = _const(n, 0, 2);
    for (int i=0; i<n; i++) {
      pa_set(ans->A, i, pa_get(a->A, i) == pa_get(b->A, i));
    }
  }
  return ans;
}




_b LessThan_bit_channel(_b x, _b y, int channel)
{
  if (_party >  2) return NULL;
  if (order(x) != 2 || order(y) != 2) {
//    printf("LessThan: x->q = %d y->q = %d\n", (int)x->q, (int)y->q);
  }
//  int q = order(x);
  int q = 2;
  int n = len(x);

  _b cx = _dup(x);
  if (_party <= 1) {
    for (int i=0; i<n; i++) {
      pa_set(cx->A, i, MOD(pa_get(x->A, i) + 1));
    }
  }
  if (_party == 2) {
    for (int i=0; i<n; i++) {
      pa_set(cx->A, i, MOD(pa_get(x->A, i)));
    }
  }

  _b cy = _dup(x);
  if (_party <= 1) {
    for (int i=0; i<n; i++) {
      pa_set(cy->A, i, MOD(pa_get(y->A, i)));
    }
  }
  if (_party == 2) {
    for (int i=0; i<n; i++) {
      pa_set(cy->A, i, MOD(pa_get(y->A, i)));
    }
  }
  _b ans = vmul_channel(cx, cy, channel);

  _free(cx);
  _free(cy);

  return ans;
}
#define LessThan_bit(x, y) LessThan_bit_channel(x, y, 0)


_b LessThan_bits_channel(_bits x, _bits y, int channel)
{
  if (_party >  2) return NULL;
  if (x->d != y->d) {
    printf("LessThan_bits: x->d = %d y->d = %d\n", x->d, y->d);
  }
  int d = x->d;
//  printf("x ");
//  _print(x->a[d-1]);
//  printf("y ");
//  _print(y->a[d-1]);
  _b lt = LessThan_bit_channel(x->a[d-1], y->a[d-1], channel);
//  printf("lt ");
//  _print(lt);
  _b eq = Equality_bit(x->a[d-1], y->a[d-1]);
//  printf("eq ");
//  _print(eq);
  for (int i=d-2; i>=0; i--) {
  //  printf("x ");
  //  _print(x->a[i]);
  //  printf("y ");
  //  _print(y->a[i]);
    _b c = LessThan_bit_channel(x->a[i], y->a[i], channel);
    _b e = Equality_bit(x->a[i], y->a[i]);
  //  printf("c ");
  //  _print(c);
  //  printf("e ");
  //  _print(e);
    _b l = AND_channel(eq, c, channel);
  //  printf("l ");
  //  _print(l);
    _move_(lt, OR_channel(lt, l, channel));
    _move_(eq, AND_channel(eq, e, channel));
  //  printf("lt ");
  //  _print(lt);
  //  printf("eq ");
  //  _print(eq);
    _free(l);
    _free(c);
    _free(e);
  }
  _free(eq);
  return lt;
}
#define LessThan_bits(x, y) LessThan_bits_channel(x, y, 0)


_b LessThan_channel(_ x, _ y, int channel)
{
  if (_party >  2) return NULL;
  _bits bx, by;
  bx = _A2B_channel(x, 2, channel);
  by = _A2B_channel(y, 2, channel);
  _b c = LessThan_bits_channel(bx, by, channel);
  _free_bits(bx);
  _free_bits(by);
#if 0
  printf("LessThan x = %d y = %d c = %d\n", debug_get(x, 0), debug_get(y, 0), debug_get(c, 0));
#endif
  return c;
}
#define LessThan(x, y) LessThan_channel(x, y, 0)



#endif
