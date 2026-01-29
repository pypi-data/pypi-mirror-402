#ifndef _FUNC_H
 #define _FUNC_H

#ifndef OF_MAX
 #define OF_MAX 4
#endif
#ifndef ONEHOT_MAX
 #define ONEHOT_MAX 4
#endif

precomp_tables PRE_B2A_tbl[MAX_CHANNELS];
precomp_tables PRE_OF_tbl[OF_MAX][MAX_CHANNELS];
precomp_tables PRE_OHA_tbl[ONEHOT_MAX][MAX_CHANNELS];
precomp_tables PRE_OHX_tbl[ONEHOT_MAX][MAX_CHANNELS];
precomp_tables PRE_OHS_tbl[ONEHOT_MAX][MAX_CHANNELS];
precomp_tables PRE_OHS3_tbl[ONEHOT_MAX][MAX_CHANNELS];
//precomp_tables PRE_RE_tbl[ONEHOT_MAX][MAX_CHANNELS];
precomp_tables PRE_OHR_tbl[ONEHOT_MAX][MAX_CHANNELS];
 
long PRE_B2A_count[MAX_CHANNELS];
long PRE_OF_count[OF_MAX][MAX_CHANNELS];
long PRE_OHA_count[ONEHOT_MAX][MAX_CHANNELS];
long PRE_OHX_count[ONEHOT_MAX][MAX_CHANNELS];
long PRE_OHS_count[ONEHOT_MAX][MAX_CHANNELS];
long PRE_OHR_count[ONEHOT_MAX][MAX_CHANNELS];

#include "share.h"
#include "precompute.h"
//#include "dshare.h"


void precomp_free_tables(precomp_tables T)
{
  if (T == NULL) return;
  precomp_free(T->TR);
  precomp_free(T->Tt);
  if (T->map != NULL) mymunmap(T->map);
  free(T);
}




typedef struct precomp_tbl_list {
  precomp_tables tbl;
  int d;
  share_t irr_poly;
  long count;
  struct precomp_tbl_list *next;
}* precomp_tbl_list;

precomp_tbl_list PRE_RE_tbl[MAX_CHANNELS];

precomp_tbl_list precomp_tbl_list_insert(precomp_tables tbl, int d, share_t irr_poly, precomp_tbl_list head)
{
  NEWT(precomp_tbl_list, list);
  list->tbl = tbl;
  list->d = d;
  list->irr_poly = irr_poly;
  list->count = 0;
  list->next = head;
  return list;
}

precomp_tables precomp_tbl_list_search(precomp_tbl_list list, int d, share_t irr_poly)
{
  precomp_tables ans = NULL;
  while (list != NULL) {
    if (list->d == d && list->irr_poly == irr_poly) {
      ans = list->tbl;
      break;
    }
    list = list->next;
  }
  return ans;
}

void precomp_tbl_list_free(precomp_tbl_list list)
{
  precomp_tbl_list next;
  while (list != NULL) {
    next = list->next;
    precomp_free_tables(list->tbl);
    free(list);
    list = next;
  }
}



////////////////////////////////////////////////////////
// f([x]_1, [x]_2) の計算
// この計算を1台でシミュレートするのは難しい?
////////////////////////////////////////////////////////
_ func1bit(_ x, share_t q, share_t *func_table)
{
  int n = x->n;
  int b = 1;
  int k = 1 << b; // 表の大きさ

  _ R = NULL, t = NULL;

// 前計算
  if (_party <= 0) {
    for (int i=0; i<k; i++) {
      for (int j=0; j<k; j++) {
      //  printf("%d ", func_table[i*k+j]);
      }
    //  printf("\n");
    }
    // P1, P2 用の表の計算

    _ F = _const(n*k*k, 0, q);
    // x1, x2 のmask用の乱数
    _ R = _const(n, 0, k);
    _ S = _const(n, 0, k);
  //  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1}; // この関数は不要?
    unsigned long *init1 = MT_init[1];
    MT m1 = MT_init_by_array(init1, 5);
  //  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
    unsigned long *init2 = MT_init[2];
    MT m2 = MT_init_by_array(init2, 5);
    for (int p=0; p<n; p++) {
      share_t r = RANDOM(m1, k);
      share_t s = RANDOM(m2, k);
      pa_set(R->A, p, r);
      pa_set(S->A, p, s);
      for (int i=0; i<k; i++) {
        for (int j=0; j<k; j++) {
          pa_set(F->A, p*k*k + i*k + j, func_table[(i^r)*k + (j^s)]);
        }
      }
    }
    MT_free(m1);
    MT_free(m2);
  //  printf("R "); _print(R);
  //  printf("S "); _print(S);
  //  printf("F "); _print(F);

    _ t0 = _const(n*k*k, 0, q);
    _ t1 = _const(n*k*k, 0, q);
    _ t2 = _const(n*k*k, 0, q);
    unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
    MT m0 = MT_init_by_array(init0, 5);
    for (int p=0; p<n; p++) {
      for (int i=0; i<k; i++) {
        for (int j=0; j<k; j++) {
          share_t rr = RANDOM(m0, q);
          pa_set(t1->A, p*k*k + i*k + j, rr);
          pa_set(t2->A, p*k*k + i*k + j, MOD(pa_get(F->A, p*k*k + i*k + j)-rr));
        }
      }
    }
    MT_free(m0);

    if (_party == 0) {
    //  printf("t0 "); _print(t0);
    //  printf("t1 "); _print(t1);
    //  printf("t2 "); _print(t2);
      mpc_send_share(TO_PARTY1, R);
      mpc_send_share(TO_PARTY2, S);
      mpc_send_share(TO_PARTY1, t1);
      mpc_send_share(TO_PARTY2, t2);
    }
  } else {
    R = _const(n, 0, k);
    mpc_recv_share(FROM_SERVER, R);
    t = _const(n*k*k, 0, q);
    mpc_recv_share(FROM_SERVER, t);
  //  printf("R "); _print(R);
  //  printf("t "); _print(t);

  }

// 本計算
  _ ans = _const(n, 0, q);
  if (_party <= 0) {
  } else {
  //  printf("x "); _print(x);
  //  printf("R "); _print(R);
    _ y = _const(n, 0, k);
    for (int p=0; p<n; p++) {
      pa_set(y->A, p, pa_get(R->A, p) ^ pa_get(x->A, p));
    }
  //  printf("y "); _print(y);
    _ z = _const(n, 0, k);
    mpc_exchange_share(y, z);
  //  printf("z "); _print(z);
    if (_party == 1) {
      for (int p=0; p<n; p++) {
      //  share_t r = pa_get(R->A, p);
        share_t xr = pa_get(y->A, p);
        share_t ys = pa_get(z->A, p);
      //  printf("p %d x %d y %d\n", p, xr, ys);
        pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys));
      }
    }
    if (_party == 2) {
      for (int p=0; p<n; p++) {
      //  share_t s = pa_get(R->A, p);
        share_t xr = pa_get(z->A, p);
        share_t ys = pa_get(y->A, p);
      //  printf("p %d x %d y %d\n", p, xr, ys);
        pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys));
      }      
    }
  }
  return ans;
}


///////////////////////////////////////////////////////////
// 前計算の表を作成
///////////////////////////////////////////////////////////
void func1bit3_precomp(int n, share_t q, share_t *func_table, char *fname)
{
  int b = 1;
  int k = 1 << b; // 表の大きさ

  if (_party > 0) goto sync;

  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);

//  precomp_table TR, Tt;

  for (int i=0; i<k; i++) {
    for (int j=0; j<k; j++) {
  //    printf("%d ", func_table[i*k+j]);
    }
  //  printf("\n");
  }
  // P1, P2 用の表の計算

  _ F = _const(n*k*k, 0, q);
  // x1, x2 のmask用の乱数
  _ R = _const(n, 0, k);
  _ S = _const(n, 0, k);
//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
  for (int p=0; p<n; p++) {
    share_t r = RANDOM(m1, k);
    share_t s = RANDOM(m2, k);
    pa_set(R->A, p, r);
    pa_set(S->A, p, s);
    for (int i=0; i<k; i++) {
      for (int j=0; j<k; j++) {
        pa_set(F->A, p*k*k + i*k + j, func_table[(i^r)*k + (j^s)]);
      }
    }
  }
  MT_free(m1);
  MT_free(m2);
  //printf("R "); _print(R);
  //printf("S "); _print(S);

  FILE *f0, *f1, *f2;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f0, n, q, init1);



  _ t1 = _const(n*k*k, 0, q);
  _ t2 = _const(n*k*k, 0, q);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);
  for (int p=0; p<n; p++) {
    for (int i=0; i<k; i++) {
      for (int j=0; j<k; j++) {
        share_t rr = RANDOM(m0, q);
        pa_set(t1->A, p*k*k + i*k + j, rr);
        pa_set(t2->A, p*k*k + i*k + j, MOD(pa_get(F->A, p*k*k + i*k + j)-rr));
      }
    }
  }
  MT_free(m0);
  precomp_write_seed(f1, n*k*k, q, init0);
  precomp_write_share(f2, t2);

// P0 は table をそのまま格納
  _ t0 = _const(k, 0, q);
  for (int i=0; i<k; i++) {
    pa_set(t0->A, i, func_table[i*k+0]);
  }
  precomp_write_share(f0, t0);

  fclose(f0);
  fclose(f1);
  fclose(f2);

  _free(F);  _free(R);  _free(S);
  _free(t0);  _free(t1);  _free(t2);
  free(fname0);  free(fname1);  free(fname2);

sync:;

  //printf("t0 "); _print(t0);
  //printf("t1 "); _print(t1);
  //printf("t2 "); _print(t2);
}


void funckbit_precomp(int b, int n, share_t q, share_t *func_table, char *fname)
{
  if (_party > 0) goto sync;
//  int b = 1;
  int k = 1 << b; // 表の大きさ


  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);

//  precomp_table TR, Tt;

  for (int i=0; i<k; i++) {
    for (int j=0; j<k; j++) {
  //    printf("%d ", func_table[i*k+j]);
    }
  //  printf("\n");
  }
  // P1, P2 用の表の計算

  _ F = _const(n*k*k, 0, q);
  // x1, x2 のmask用の乱数
  _ R = _const(n, 0, k);
  _ S = _const(n, 0, k);
//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
  for (int p=0; p<n; p++) {
    share_t r = RANDOM(m1, k);
    share_t s = RANDOM(m2, k);
    pa_set(R->A, p, r);
    pa_set(S->A, p, s);
    for (int i=0; i<k; i++) {
      for (int j=0; j<k; j++) {
        pa_set(F->A, p*k*k + i*k + j, func_table[(i^r)*k + (j^s)]);
      }
    }
  }
  MT_free(m1);
  MT_free(m2);
  //printf("R "); _print(R);
  //printf("S "); _print(S);

  FILE *f0, *f1, *f2;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f0, n, q, init1);



  _ t1 = _const(n*k*k, 0, q);
  _ t2 = _const(n*k*k, 0, q);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);
  for (int p=0; p<n; p++) {
    for (int i=0; i<k; i++) {
      for (int j=0; j<k; j++) {
        share_t rr = RANDOM(m0, q);
        pa_set(t1->A, p*k*k + i*k + j, rr);
        pa_set(t2->A, p*k*k + i*k + j, MOD(pa_get(F->A, p*k*k + i*k + j)-rr));
      //  pa_set(t2->A, p*k*k + i*k + j, MOD(pa_get(F->A, p*k*k + i*k + j) ^ rr)); // 加法的シェアではなく xor にする?
      }
    }
  }
  MT_free(m0);
  precomp_write_seed(f1, n*k*k, q, init0);
  precomp_write_share(f2, t2);

// P0 は table をそのまま格納
  _ t0 = _const(k, 0, q);
  for (int i=0; i<k; i++) {
    pa_set(t0->A, i, func_table[i*k+0]);
  }
  precomp_write_share(f0, t0);

  fclose(f0);
  fclose(f1);
  fclose(f2);

  _free(F);  _free(R);  _free(S);
  _free(t0);  _free(t1);  _free(t2);
  free(fname0);  free(fname1);  free(fname2);

sync:;

  //printf("t0 "); _print(t0);
  //printf("t1 "); _print(t1);
  //printf("t2 "); _print(t2);
}


///////////////////////////////////////////////////////////
// 前計算の表を読み込む
///////////////////////////////////////////////////////////
precomp_tables func1bit3_read(char *fname)
{
//  if (_party == 0) return NULL;
  if (_party >  2) return NULL;
  int party = _party;
//  if (_party <= 0) {
  if (_party < 0) {
  //  NEWT(precomp_tables, T);
  //  T->map = NULL;
  //  T->TR = NULL;
  //  T->Tt = NULL;
  //  return T;
    party = 0;
  }
  char *fname2 = precomp_fname(fname, party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  //printf("party %d map %p\n", party, map);

  return T;
}

///////////////////////////////////////////////////////////
// 前計算の表を使って計算
///////////////////////////////////////////////////////////
_ func1bit3_channel(_ x, share_t q, precomp_tables T, int channel)
{
  int n = x->n;
  int b = 1;
  int k = 1 << b; // 表の大きさ

//  if (_party == 0) return NULL;

  _ ans = _const(n, 0, q);

  if (_party <= 0) {
    pa_iter itr_ans = pa_iter_new(ans->A);
    pa_iter itr_x = pa_iter_new(x->A);
    for (int p=0; p<n; p++) {
    //  share_t xx = pa_get(x->A, p);
      //share_t xx = pa_get(x->A, p) % k;
      share_t xx = pa_iter_get(itr_x) % k;
    //  pa_set(ans->A, p, pa_get(T->Tt->u.share.a, xx*k + 0)%q);
      //pa_set(ans->A, p, pa_get(T->Tt->u.share.a, xx)%q);
      pa_iter_set(itr_ans, pa_get(T->Tt->u.share.a, xx)%q);
    }
    pa_iter_flush(itr_ans); pa_iter_free(itr_x);
    return ans;
  }


  _ t = _const(n*k*k, 0, q);
  pa_iter itr_t = pa_iter_new(t->A);
  for (int p=0; p<n*k*k; p++) {
    //pa_set(t->A, p, precomp_get(T->Tt)%q);
    pa_iter_set(itr_t, precomp_get(T->Tt)%q);
  }
  pa_iter_flush(itr_t);
  //printf("x "); _print(x);
  _ y = _const(n, 0, k);
  pa_iter itr_y = pa_iter_new(y->A);
  pa_iter itr_x = pa_iter_new(x->A);
  for (int p=0; p<n; p++) {
    //pa_set(y->A, p, (precomp_get(T->TR) ^ pa_get(x->A, p))%k);
    pa_iter_set(itr_y, (precomp_get(T->TR) ^ pa_iter_get(itr_x))%k);
  }
  pa_iter_flush(itr_y); pa_iter_free(itr_x);
  //printf("y "); _print(y);
  _ z = _const(n, 0, k);
  mpc_exchange_share_channel(y, z, channel);
  //printf("z "); _print(z);
  if (_party == 1) {
    pa_iter itr_y = pa_iter_new(y->A);
    pa_iter itr_z = pa_iter_new(z->A);
    pa_iter itr_ans = pa_iter_new(ans->A);
    for (int p=0; p<n; p++) {
      //share_t xr = pa_get(y->A, p);
      //share_t ys = pa_get(z->A, p);
      share_t xr = pa_iter_get(itr_y);
      share_t ys = pa_iter_get(itr_z);
      //pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys)%q);
      pa_iter_set(itr_ans, pa_get(t->A, p*k*k + xr*k + ys)%q);
    }
    pa_iter_flush(itr_ans); pa_iter_free(itr_y); pa_iter_free(itr_z);
  }
  if (_party == 2) {
    pa_iter itr_y = pa_iter_new(y->A);
    pa_iter itr_z = pa_iter_new(z->A);
    pa_iter itr_ans = pa_iter_new(ans->A);
    for (int p=0; p<n; p++) {
      //share_t xr = pa_get(z->A, p);
      //share_t ys = pa_get(y->A, p);
      share_t xr = pa_iter_get(itr_z);
      share_t ys = pa_iter_get(itr_y);
      //pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys)%q);
      pa_iter_set(itr_ans, pa_get(t->A, p*k*k + xr*k + ys)%q);
    }
    pa_iter_flush(itr_ans); pa_iter_free(itr_y); pa_iter_free(itr_z);
  }
  _free(y);  _free(z);  _free(t);
  return ans;
}
#define func1bit3(x, q, T) func1bit3_channel(x, q, T, 0)
#define func1bit(x, q, T) func1bit3_channel(x, q, T, 0)
#define func1bit_channel(x, q, T, c) func1bit3_channel(x, q, T, c)


precomp_tables funckbit_read(char *fname)
{
//  if (_party == 0) return NULL;
  if (_party > 2) return NULL;
  char *fname2 = precomp_fname(fname, _party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}

_ funckbit_channel(int b, _ x, share_t q, precomp_tables T, int channel)
{
  int n = x->n;
//  int b = 1;
  int k = 1 << b; // 表の大きさ

//  if (_party == 0) return NULL;

  _ ans = _const(n, 0, q);

  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      pa_set(ans->A, p, pa_get(T->Tt->u.share.a, xx*k + 0)%q);
    }
    return ans;
  }


  _ t = _const(n*k*k, 0, q);
  for (int p=0; p<n*k*k; p++) {
    pa_set(t->A, p, precomp_get(T->Tt)%q);
  }
//  printf("x "); _print(x);
  _ y = _const(n, 0, k);
  for (int p=0; p<n; p++) {
    pa_set(y->A, p, (precomp_get(T->TR) ^ pa_get(x->A, p))%k); // x は加法的シェアだが，xor で大丈夫?
  }
//  printf("y "); _print(y);
  _ z = _const(n, 0, k);
  mpc_exchange_share_channel(y, z, channel);
//  printf("z "); _print(z);
  if (_party == 1) {
    for (int p=0; p<n; p++) {
      share_t xr = pa_get(y->A, p);
      share_t ys = pa_get(z->A, p);
      pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys)%q);
    }
  }
  if (_party == 2) {
    for (int p=0; p<n; p++) {
      share_t xr = pa_get(z->A, p);
      share_t ys = pa_get(y->A, p);
      pa_set(ans->A, p, pa_get(t->A, p*k*k + xr*k + ys)%q);
    }      
  }
  _free(y);  _free(z);  _free(t);
  return ans;
}
#define funckbit(b, x, q, T) funckbit_channel(b, x, q, T, 0)


_ funckbit_online_channel(int b, _ x, share_t q, share_t *func_table, int channel)
{
  int n = len(x);
  funckbit_precomp(b, n, q, func_table, "funcktmp.dat");
//  sync();
  precomp_tables tbl = funckbit_read("funcktmp.dat");
  return funckbit_channel(b, x, q, tbl, channel);
}
#define funckbit_online(b, x, q, func_table) funckbit_online_channel(b, x, q, func_table, 0)


void of_tbl_init(void)
{
  for (int i=0; i<_opt.channels; i++) {
    for (int j=1; j<=OF_MAX; j++) {
      PRE_OF_tbl[j-1][i] = NULL;
      PRE_OF_count[j-1][i] = 0;
    }
  }
}

void of_tbl_read(int d, int channel, char *fname)
{
  PRE_OF_tbl[d-1][channel] = func1bit3_read(fname);
}

void b2a_tbl_init(void)
{
  for (int i=0; i<_opt.channels; i++) {
    PRE_B2A_tbl[i] = NULL;
    PRE_B2A_count[i] = 0;
  }
}

void b2a_tbl_read(int channel, char *fname)
{
  PRE_B2A_tbl[channel] = func1bit3_read(fname);
}

void onehot_tbl_init(void)
{
  for (int i=0; i<_opt.channels; i++) {
    for (int j=1; j<=ONEHOT_MAX; j++) {
      PRE_OHA_tbl[j-1][i] = NULL;
      PRE_OHX_tbl[j-1][i] = NULL;
      PRE_OHS_tbl[j-1][i] = NULL;
      PRE_OHR_tbl[j-1][i] = NULL;
      PRE_OHA_count[j-1][i] = 0;
      PRE_OHX_count[j-1][i] = 0;
      PRE_OHS_count[j-1][i] = 0;
      PRE_OHR_count[j-1][i] = 0;
    }
  }
}

precomp_tables onehotvec_read(char *fname)
{
//  if (_party == 0) return NULL;
  int party = _party;
  if (party < 0) party = 0;
  char *fname2 = precomp_fname(fname, party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}

precomp_tables onehotvec_shamir3_read(char *fname)
{
//  if (_party == 0) return NULL;
  int party = _party;
  if (party < 0) party = 0;
  char *fname2 = precomp_fname(fname, party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}

precomp_tables onehotvec_rss_read(char *fname)
{
//  if (_party == 0) return NULL;
  int party = _party;
  if (party < 0) party = 0;
  char *fname2 = precomp_fname(fname, party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}

precomp_tables shamir3_revert_read(char *fname)
{
//  if (_party == 0) return NULL;
  int party = _party;
  if (party < 0) party = 0;
  char *fname2 = precomp_fname(fname, party);

  NEWT(precomp_tables, T);

  MMAP *map = NULL;
  map = mymmap(fname2);
  uchar *p = (uchar *)map->addr;
  T->TR = precomp_read(&p);
  T->Tt = precomp_read(&p);
  T->map = map;

  free(fname2);

  return T;
}


void onehot_tbl_read(int d, int xor, int channel, char *fname)
{
  if (d < 1 || d > ONEHOT_MAX) {
    printf("onehot_tbl_read: d = %d MAX = %d\n", d, ONEHOT_MAX);
    exit(1);
  }
  if (xor) {
    PRE_OHX_tbl[d-1][channel] = onehotvec_read(fname);
  } else {
    PRE_OHA_tbl[d-1][channel] = onehotvec_read(fname);
  }
}

void onehot_shamir_tbl_read(int d, int channel, char *fname)
{
  if (d < 1 || d > ONEHOT_MAX) {
    printf("onehot_shamir_tbl_read: d = %d MAX = %d\n", d, ONEHOT_MAX);
    exit(1);
  }
  PRE_OHS_tbl[d-1][channel] = onehotvec_read(fname);
  //printf("PRE_OHS_tbl d=%d channel=%d\n", d, channel);
}

void onehot_rss_tbl_read(int d, share_t irr_poly, int channel, char *fname)
{
  if (d < 1 || d > ONEHOT_MAX) {
    printf("onehot_rss_tbl_read: d = %d MAX = %d\n", d, ONEHOT_MAX);
    exit(1);
  }
  PRE_OHR_tbl[d-1][channel] = onehotvec_rss_read(fname);
}

void onehot_shamir3_tbl_read(int d, share_t irr_poly, int channel, char *fname)
{
//  int d = blog(irr_poly);
  if (d < 1 || d > ONEHOT_MAX) {
    printf("onehot_shamir3_tbl_read: d = %d MAX = %d\n", d, ONEHOT_MAX);
    exit(1);
  }
  PRE_OHS3_tbl[d-1][channel] = onehotvec_shamir3_read(fname);
}

void shamir3_revert_tbl_read(int d, share_t irr_poly, int channel, char *fname)
{
  //int d = blog(irr_poly);
//  PRE_RE_tbl[d-1][channel] = shamir3_revert_read(fname);
  precomp_tables tbl = shamir3_revert_read(fname);
  PRE_RE_tbl[channel] = precomp_tbl_list_insert(tbl, d, irr_poly, PRE_RE_tbl[channel]);
}


void onehotvec_precomp(int b, int n, share_t q, char *fname, int xor)
{
//  int b = 1;
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  if (_party > 0) goto sync;

  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);

  _ F = _const(n*w, 0, q);
  // x1, x2 のmask用の乱数
  _ R = _const(n, 0, k);
  _ S = _const(n, 0, k);
//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
  for (int p=0; p<n; p++) {
    share_t r = RANDOM(m1, k);
    share_t s = RANDOM(m2, k);
    share_t t;
  //  r = s = 0; // test
    if (xor) {
      t = r ^ s;
    } else {
      t = (r + s) % k;
    }
    pa_set(R->A, p, r);
    pa_set(S->A, p, s);
    for (int j=0; j<w; j++) {
      if (xor) {
      //  pa_set(F->A, p*k*w + i*w + j, func_table[(i^t)*w + j]);
        int z = (t == j);
        pa_set(F->A, p*w + j, z);
      } else {
      //  pa_set(F->A, p*k*w + i*w + j, func_table[((i+t)%k)*w + j]);
        int z = (t == j);
        pa_set(F->A, p*w + j, z);
      }
    }
  }
  MT_free(m1);
  MT_free(m2);
  //printf("R "); _print(R);
  //printf("S "); _print(S);

  FILE *f0, *f1, *f2;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f0, n, q, init1);



  _ t1 = _const(n*w, 0, q);
  _ t2 = _const(n*w, 0, q);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);
  for (int p=0; p<n; p++) {
    for (int j=0; j<w; j++) {
      share_t rr = RANDOM(m0, q);
      pa_set(t1->A, p*w + j, rr);
      pa_set(t2->A, p*w + j, MOD(pa_get(F->A, p*w + j)-rr));
    }
  }
  MT_free(m0);
  precomp_write_seed(f1, n*w, q, init0);
  precomp_write_share(f2, t2);

// P0 は table をそのまま格納
  _ t0 = _const(w, 0, q);
  for (int j=0; j<w; j++) {
    pa_set(t0->A, j, (j == 0)); // 要確認
  }
  precomp_write_share(f0, t0);

  fclose(f0);
  fclose(f1);
  fclose(f2);

//  printf("t0 "); _print(t0);
//  printf("t1 "); _print(t1);
//  printf("t2 "); _print(t2);

  _free(F);  _free(R);  _free(S);
  _free(t0);  _free(t1);  _free(t2);
  free(fname0);  free(fname1);  free(fname2);

sync:;

}

_ onehotvec_table_channel(int b, _ x, share_t q, precomp_tables T, int xor, int channel)
{
  int n = x->n;
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  _ ans = _const(n*w, 0, q);

  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      for (int j=0; j<w; j++) {
        pa_set(ans->A, p*w+j, pa_get(T->Tt->u.share.a, xx*w + j)%q);
      }
    }
    return ans;
  }

  _ t = _const(n*w, 0, q);
  for (int p=0; p<n*w; p++) {
    pa_set(t->A, p, precomp_get(T->Tt)%q);
  }
//  printf("t "); _print(t);

//  printf("x "); _print(x);


  _ y = _const(n, 0, k);
  for (int p=0; p<n; p++) {
    if (xor) {
      pa_set(y->A, p, (precomp_get(T->TR) ^ pa_get(x->A, p))%k);
    } else {
    //  pa_set(y->A, p, (precomp_get(T->TR) + pa_get(x->A, p))%k); // !!!
      pa_set(y->A, p, (k - precomp_get(T->TR) + pa_get(x->A, p))%k);
    }
  }
//  printf("y "); _print(y);
  _ z = _const(n, 0, k);
  mpc_exchange_share_channel(y, z, channel);
//  printf("z "); _print(z);
  if (_party == 1 || _party == 2) {
    for (int p=0; p<n; p++) {
      share_t xr = pa_get(y->A, p);
      share_t ys = pa_get(z->A, p);
      share_t tt;
      if (xor) {
        tt = xr ^ ys; // 入力は xor のシェア
      } else {
        tt = (xr + ys) % k; // 入力は加法的シェア
      }
      for (int j=0; j<w; j++) {
      //  pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + tt*w + j)%q);
        share_t z;
        if (xor) {
          z = tt ^ j;
        } else {
          z = (k + j - tt) % k;
        }
        pa_set(ans->A, p*w+j, pa_get(t->A, p*w + z)%q);
      }
    }
  }
  _free(y);  _free(z);  _free(t);
  return ans;
}
#define onehotvec_table(b, x, q, T, xor) onehotvec_table_channel(b, x, q, T, xor, 0)


_ onehotvec_online_channel(_ x, share_t q, int xor, int channel)
{
  if (_party > 2) return NULL;
  int n = x->n;
  int b = blog(order(x)-1)+1;
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  _ R = NULL, t = NULL;

// 前計算
  if (_party <= 0) {
    // P1, P2 用の表の計算

    _ F = _const(n*w, 0, q);
    // x1, x2 のmask用の乱数
    _ R = _const(n, 0, k);
    _ S = _const(n, 0, k);
  //  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  //  MT m1 = MT_init_by_array(init1, 5);
    MT m1 = MT_init_by_array(MT_init[1], 5);
  //  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  //  MT m2 = MT_init_by_array(init2, 5);
    MT m2 = MT_init_by_array(MT_init[2], 5);
    for (int p=0; p<n; p++) {
      share_t r = RANDOM(m1, k);
      share_t s = RANDOM(m2, k);
      //r = s = 0; // test
      share_t t;
      if (xor) {
        t = r ^ s;
      } else {
        t = (r + s) % k;
      }
      pa_set(R->A, p, r);
      pa_set(S->A, p, s);
      for (int j=0; j<w; j++) {
        if (xor) {
        //  pa_set(F->A, p*k*w + i*w + j, func_table[(i^t)*w + j]);
        //  int z = func_table[(i^t)*w + j];
          int z = (t == j);
          pa_set(F->A, p*w + j, z);
        } else {
        //  pa_set(F->A, p*k*w + i*w + j, func_table[((i+t)%k)*w + j]);
        //  int z = func_table[((i+t)%k)*w + j];
          int z = (t == j);
          pa_set(F->A, p*w + j, z);
        }
      }
    }
    MT_free(m1);
    MT_free(m2);
  //  printf("R "); _print(R);
  //  printf("S "); _print(S);
  //  printf("F "); _print(F);

    _ t0 = _const(n*w, 0, q);
    _ t1 = _const(n*w, 0, q);
    _ t2 = _const(n*w, 0, q);
  //  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
    unsigned long *init0 = MT_init[0];
    MT m0 = MT_init_by_array(init0, 5); // 要修正
    for (int p=0; p<n; p++) {
      for (int j=0; j<w; j++) {
        share_t rr = RANDOM(m0, q);
      //  rr = 0;
        pa_set(t1->A, p*w + j, rr);
        pa_set(t2->A, p*w + j, MOD(pa_get(F->A, p*w + j)-rr)); // 答えは加法的シェア
      }
    }
    MT_free(m0);

    if (_party == 0) {
    //  printf("t0 "); _print(t0);
    //  printf("t1 "); _print(t1);
    //  printf("t2 "); _print(t2);
      mpc_send_share_channel(TO_PARTY1, R, channel);
      mpc_send_share_channel(TO_PARTY2, S, channel);
      mpc_send_share_channel(TO_PARTY1, t1, channel);
      mpc_send_share_channel(TO_PARTY2, t2, channel);
    }
    _free(t0);
    _free(t1);
    _free(t2);
    _free(F);
    _free(R);
    _free(S);
  } else {
    R = _const(n, 0, k);
    mpc_recv_share_channel(FROM_SERVER, R, channel);
    //printf("R "); _print(R);
    t = _const(n*w, 0, q);
    mpc_recv_share_channel(FROM_SERVER, t, channel);
    //printf("t "); _print(t);

  }

// 本計算
  _ ans = _const(n*w, 0, q);
  if (_party <= 0) {
    for (int p=0; p<n; p++) {
      share_t xx = pa_get(x->A, p);
      for (int j=0; j<w; j++) {
      //  pa_set(ans->A, p*w+j, func_table[xx*w+j]%q);
      //  int z = func_table[xx*w+j];
        int z = (xx) == (j);
        pa_set(ans->A, p*w+j, z % q);
      }
    }
  } else {
  //  printf("x "); _print(x);
  //  printf("R "); _print(R);
    _ y = _const(n, 0, k);
    for (int p=0; p<n; p++) {
      if (xor) {
        pa_set(y->A, p, (pa_get(R->A, p) ^ pa_get(x->A, p))%k);
      } else {
        pa_set(y->A, p, (k - pa_get(R->A, p) + pa_get(x->A, p))%k);
      }
    }
  //  printf("y "); _print(y);
    _ z = _const(n, 0, k);
    mpc_exchange_share_channel(y, z, channel);
  //  printf("z "); _print(z);
    if (_party == 1 || _party == 2) {
      for (int p=0; p<n; p++) {
        share_t xr = pa_get(y->A, p);
        share_t ys = pa_get(z->A, p);
        share_t tt;
        if (xor) {
          tt = xr ^ ys; // 入力は xor のシェア
        } else {
          tt = (xr + ys) % k; // 入力は加法的シェア
        }
      //  printf("p %d x %d y %d\n", p, xr, ys);
        for (int j=0; j<w; j++) {
        //  pa_set(ans->A, p*w+j, pa_get(t->A, p*k*w + tt*w + j)%q);
          share_t z;
          if (xor) {
            z = tt ^ j;
          } else {
            z = (k + j - tt) % k;
          }
          pa_set(ans->A, p*w+j, pa_get(t->A, p*w + z)%q);
        }
      }
    }
    _free(y);
    _free(z);
    _free(R);
    _free(t);
  }
  return ans;
}
#define onehotvec_online(x, q, xor) onehotvec_online_channel(x, q, xor, 0)

///////////////////////////////////////////////////////////////////////////
// One-hot vector
// 入力: 22ADD (算術 or XOR) xor で指定
// 出力: 22ADD
///////////////////////////////////////////////////////////////////////////
_ onehotvec_channel(_ x, share_t q, int xor, int channel)
{
//  int n = x->n;
  int d = blog(order(x)-1)+1;
  if (d < 1 || d > ONEHOT_MAX) {
    printf("onehotvec: d=%d MAX=%d\n", d, ONEHOT_MAX);
    exit(1);
  }
  precomp_tables T = NULL;
  if (xor) {
    T = PRE_OHX_tbl[d-1][channel];
  } else {
    T = PRE_OHA_tbl[d-1][channel];
  }
  if (T != NULL) {
    if (xor) {
      PRE_OHX_count[d-1][channel] += len(x);
    } else {
      PRE_OHA_count[d-1][channel] += len(x);
    }
    return onehotvec_table_channel(d, x, q, T, xor, channel);
  } else {
    return onehotvec_online_channel(x, q, xor, channel);
  }
}
#define onehotvec(x, q, xor) onehotvec_channel(x, q, xor, 0)




void onehotvec_shamir_precomp(int b, int n, share_t q, char *fname)
{
  int k = 1 << b; // 表の大きさ
  int w = 1 << b; // ベクトルの長さ

  if (_party > 0) goto sync;

  char *fname0 = precomp_fname(fname, 0);
  char *fname1 = precomp_fname(fname, 1);
  char *fname2 = precomp_fname(fname, 2);
  char *fname3 = precomp_fname(fname, 3);

  _ F = _const(n*w, 0, q);
  // x1, x2 のmask用の乱数
  _ R = _const(n, 0, k);
  _ S = _const(n, 0, k);
//  unsigned long init1[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init1 = MT_init[1];
  MT m1 = MT_init_by_array(init1, 5);
//  unsigned long init2[5]={0x123, 0x234, 0x345, 0x456, 2};
  unsigned long *init2 = MT_init[2];
  MT m2 = MT_init_by_array(init2, 5);
  for (int p=0; p<n; p++) {
    share_t r = RANDOM(m1, k);
    share_t s = RANDOM(m2, k);
    share_t t;
  //  r = s = 0; // test
    t = (r + s) % k;
    pa_set(R->A, p, r);
    pa_set(S->A, p, s);
    for (int j=0; j<w; j++) {
    //  pa_set(F->A, p*k*w + i*w + j, func_table[((i+t)%k)*w + j]);
      int z = (t == j);
      pa_set(F->A, p*w + j, z);
    }
  }
  MT_free(m1);
  MT_free(m2);
  //printf("R "); _print(R);
  //printf("S "); _print(S);

  FILE *f0, *f1, *f2, *f3;
  f0 = fopen(fname0, "wb");
  f1 = fopen(fname1, "wb");
  f2 = fopen(fname2, "wb");
  f3 = fopen(fname3, "wb");
  precomp_write_seed(f1, n, q, init1);
  precomp_write_seed(f2, n, q, init2);
  precomp_write_seed(f3, n, q, init1); // 使わない?
  precomp_write_seed(f0, n, q, init1); // 使わない?



  _ t1 = _const(n*w, 0, q);
  _ t2 = _const(n*w, 0, q);
  _ t3 = _const(n*w, 0, q);
//  unsigned long init0[5]={0x123, 0x234, 0x345, 0x456, 1};
  unsigned long *init0 = MT_init[0];
  MT m0 = MT_init_by_array(init0, 5);
  for (int p=0; p<n; p++) {
    for (int j=0; j<w; j++) {
      share_t rr = RANDOM(m0, q);
      share_t x = pa_get(F->A, p*w + j);
      pa_set(t1->A, p*w + j, MOD(x + 1 * rr));
      pa_set(t2->A, p*w + j, MOD(x + 2 * rr));
      pa_set(t3->A, p*w + j, MOD(x + 3 * rr));
    }
  }
  MT_free(m0);
  precomp_write_share(f1, t1);
  precomp_write_share(f2, t2);
  precomp_write_share(f3, t3);

// P0 は table をそのまま格納
  _ t0 = _const(w, 0, q);
  for (int j=0; j<w; j++) {
    pa_set(t0->A, j, (j == 0)); // 要確認
  }
  precomp_write_share(f0, t0);

  fclose(f0);
  fclose(f1);
  fclose(f2);
  fclose(f3);

  _free(F);  _free(R);  _free(S);
  _free(t0);  _free(t1);  _free(t2);  _free(t3);
  free(fname0);  free(fname1);  free(fname2);  free(fname3);

sync:;

}


_ overflow1_online_channel(_b a, share_t q, int channel);

_ overflow_channel(int d, _ b, share_t q, int channel)
{
  if (1 <= d && d <= OF_MAX && PRE_OF_tbl[d-1][channel] != NULL) {
    PRE_OF_count[d-1][channel] += len(b);
    return funckbit_channel(d, b, q, PRE_OF_tbl[d-1][channel], channel);
  }
  if (d == 1) {
    return overflow1_online_channel(b, q, channel);
  }
  printf("overflow_channel: d = %d\n", d);
  exit(1);
}
#define overflow(d, bb, q) overflow_channel(d, bb, q, 0)


static _bits share_const_bits(int n, share_t v, share_t q, int d);
static _bits share_const_bits_3party(int n, share_t v, share_t q, int d);


////////////////////////////////////////////////////////////////////////////////
// 表は公開
////////////////////////////////////////////////////////////////////////////////
_bits tablelookup(_ x, share_t *tbl, share_t q, int xor)
{
  int n = len(x);
  int k = blog(q-1)+1; // 出力の桁数
  share_t w = order(x);

//  _bits ans = share_const_bits(n, 0, q, k);
  _bits ans = share_const_bits(n, 0, 2, k);

  //_ ohv = onehotvec_online(x, q, xor); // 長さ w の one hot vector が n 個
  //_ ohv = onehotvec(x, q, xor); // 長さ w の one hot vector が n 個
  _ ohv = onehotvec(x, 2, xor); // 長さ w の one hot vector が n 個
//  printf("ohv "); _print(ohv);

  for (int i=0; i<n; i++) {
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
  return ans;
}

#endif
