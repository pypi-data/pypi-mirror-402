#ifndef _PRECOMPUTE_H
 #define _PRECOMPUTE_H

//#include "share.h"
#include "mman.h"

/**********************************************************************
 * 前計算してディスクに格納
 * シェアを格納するか，乱数の種を格納
 * 
**********************************************************************/

#define ID_PRECOMP 0x1B


#define PRECOMP_SEED 1
#define PRECOMP_SHARE 2

typedef struct {
  int type; // seed か share か
  union {
    struct {
      MT r;
      int n;
      //share_t q;
      unsigned long seed[5];
    } seed;
    struct {
      packed_array a;
    } share;
  } u;
  share_t q; // 未使用
  int current;    // 次に使う要素の位置
}* precomp_table;

typedef struct {
  precomp_table TR, Tt;
  MMAP *map;
}* precomp_tables;



char *precomp_fname(char *fname, int party)
{
  if (party < 0) party = 0;
  char *fname2;
  NEWA(fname2, char, strlen(fname)+3);
  sprintf(fname2, "%s.%1d", fname, party);

  return fname2;
}


void precomp_write_seed(FILE *f, int n, share_t q, unsigned long seed[5])
{
  writeuint(1,ID_PRECOMP,f);
  writeuint(1,PRECOMP_SEED,f);
  writeuint(sizeof(n),n,f);
  writeuint(sizeof(q),q,f);
  for (int i=0; i<5; i++) {
    writeuint(sizeof(seed[0]), seed[i], f);
  }
}

precomp_table precomp_table_new_seed(int n, share_t q, unsigned long seed[5])
{
  NEWT(precomp_table, T); 
  T->type = PRECOMP_SEED;
  T->current = 0;

  T->u.seed.n = n;
  //T->u.seed.q = q;
  T->q = q;
  for (int i=0; i<5; i++) {
    T->u.seed.seed[i] = seed[i];
  }
  T->u.seed.r = MT_init_by_array(T->u.seed.seed, 5);

  return T;
}

#if 0
void precomp_write_share_old(FILE *f, packed_array a)
{
  writeuint(1,ID_PRECOMP,f);
  writeuint(1,PRECOMP_SHARE,f);
  pa_write(a, f);
}
#endif

void precomp_write_pa(FILE *f, packed_array a, share_t q)
{
  writeuint(1,ID_PRECOMP,f);
  writeuint(1,PRECOMP_SHARE,f);
  writeuint(sizeof(q),q,f); // 追加
  pa_write(a, f);
}

void precomp_write_share(FILE *f, share_array a)
{
//  writeuint(1,ID_PRECOMP,f);
//  writeuint(1,PRECOMP_SHARE,f);
//  writeuint(sizeof(a->q),a->q,f); // 追加
//  pa_write(a->A, f);
  precomp_write_pa(f, a->A, a->q);
}



precomp_table precomp_table_new_share(packed_array a)
{
  NEWT(precomp_table, T); 
  T->type = PRECOMP_SHARE;
  T->current = 0;

  T->u.share.a = a;

  return T;
}

void precomp_write(FILE *f, precomp_table T)
{
  if (T->type == PRECOMP_SEED) {
  //  precomp_write_seed(f, T->u.seed.n, T->u.seed.q, T->u.seed.seed);
    precomp_write_seed(f, T->u.seed.n, T->q, T->u.seed.seed);
  } else if (T->type == PRECOMP_SHARE) {
    precomp_write_pa(f, T->u.share.a, T->q);
  }
}

precomp_table precomp_read(uchar **addr)
{
  uchar *p = *addr;
  NEWT(precomp_table, T);

  int id = getuint(p,0,1);  p += 1;
  if (id != ID_PRECOMP) {
    printf("precomp_read: id = %d is not supported.\n", id);
    exit(1);
  }
  int type = getuint(p,0,1);  p += 1;
  T->type = type;
  if (type == PRECOMP_SEED) {
    T->u.seed.n = getuint(p,0,sizeof(T->u.seed.n));  p += sizeof(T->u.seed.n);
    T->q = getuint(p,0,sizeof(T->q));  p += sizeof(T->q);
    for (int i=0; i<5; i++) {
      T->u.seed.seed[i] = getuint(p,0,sizeof(T->u.seed.seed[0]));  p += sizeof(T->u.seed.seed[0]);
    }
    T->u.seed.r = MT_init_by_array(T->u.seed.seed, 5);
  } else if (type == PRECOMP_SHARE) {
    T->q = getuint(p,0,sizeof(T->q));  p += sizeof(T->q);
    T->u.share.a = pa_read(&p);
  } else {
    printf("precomp_read: type = %d is not supported.\n", type);
    exit(1);
  }

  T->current = 0;
  *addr = p;
  return T;
}

share_t precomp_order(precomp_table T)
{
  share_t q;
  q = T->q;
  return q;

}

share_t precomp_get(precomp_table T)
{
  share_t x;
  if (T->type == PRECOMP_SEED) {
    x = RANDOM(T->u.seed.r, T->q);
    T->current += 1;
    if (T->current == T->u.seed.n) {
      MT_free(T->u.seed.r);
      T->u.seed.r = MT_init_by_array(T->u.seed.seed, 5);
      T->current = 0;
    }
  } else if (T->type == PRECOMP_SHARE) {
  //  printf("current %d n %ld\n", T->current, T->u.share.a->n);
    x = pa_get(T->u.share.a, T->current);
    T->current += 1;
    if (T->current == T->u.share.a->n) {
      T->current = 0;
    }
  } else {
    printf("precomp_get: type = %d is not supported.\n", T->type);
    exit(1);
  }
  return x;
}

void precomp_free(precomp_table T)
{
  if (T == NULL) return;
  if (T->type == PRECOMP_SEED) {
    MT_free(T->u.seed.r);
  } else if (T->type == PRECOMP_SHARE) {
    pa_free_map(T->u.share.a);
  }
  free(T);
}

#if 0
precomp_tables precomp_tables_new2()
{
  precomp_tables T;
//  NEWT(precomp_table, T->TR);
//  NEWT(precomp_table, T->Tt);
  T->map = NULL;
  return T;
}

void precomp_set_seed(precomp_table T, int n, share_t q, unsigned long seed[5])
{
}
#endif

#endif
