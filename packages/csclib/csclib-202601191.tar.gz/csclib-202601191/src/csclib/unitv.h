#ifndef _UNITV_H
#define _UNITV_H

#include <stdio.h>
#include <stdlib.h>

//#include "share_core.h"
//#include "precompute.h"

typedef struct {
    int n;
    int old_q;
    int new_q;
    share_array r;
    share_array z;
    share_t *z_raw;
}* unitv_correlated_randomness;

typedef struct {
    int n;
    int l;
    int new_q;
    share_array r;
    share_array z;
    share_t *z_raw;
}* unitvb_correlated_randomness;

void unitv_cr_free(unitv_correlated_randomness cr) {
    share_free(cr->r);
    share_free(cr->z);
    if (cr->z_raw) free(cr->z_raw);
    free(cr);
}

void unitvb_cr_free(unitvb_correlated_randomness cr) {
    share_free(cr->r);
    share_free(cr->z);
    if (cr->z_raw) free(cr->z_raw);
    free(cr);
}

// オンラインでの相関係数の計算
unitv_correlated_randomness Unitv_prep_channel(int n, share_t input_q, share_t output_q, int channel) {
    share_t *R, *Z;
    share_array r, e;
    if (_party <= 0) {
        NEWA(R, share_t, n);
        NEWA(Z, share_t, n*input_q);
        memset(Z, 0, sizeof(share_t) * n*input_q);
        for (int i = 0; i < n; ++i) {
            //R[i] = RANDOM(mt0, input_q);
            R[i] = RANDOM(mt_[0][channel], input_q);
            Z[i*input_q+R[i]] = 1;
        }
        
    }

    r = share_new_channel(n, input_q, R, channel);   // ここ二つの通信を並列化したい
    e = share_new_channel(n*input_q, output_q, Z, channel);

    NEWT(unitv_correlated_randomness, cr);
    if (_party <= 0) {
      free(R); 
      //free(Z);
      cr->z_raw = Z;      
    } else {
      cr->z_raw = pa_unpack(e->A);
    }

    cr->n = n;
    cr->old_q = input_q;
    cr->new_q = output_q;
    cr->r = r;
    cr->z = e;
    return cr;
}
#define Unitv_prep(n, m) Unitv_prep_channel(n, m, 0)


unitvb_correlated_randomness Unitvb_prep_channel(int n, int l, share_t new_q, int channel) {
    share_t *R, *Z;
    share_array r;
    share_array z;

    if (_party <= 0) {
        NEWA(R, share_t, n * l);
        NEWA(Z, share_t, n * (1<<l));
        memset(Z, 0, sizeof(share_t) * n * (1<<l));
        for (int i = 0; i < n; ++i) {
            share_t x = 0;
            for (int j = 0; j < l; ++j) {
                x <<= 1;
                //R[l * (i+1) - 1 - j] = RANDOM(mt0, 2);
                R[l * (i+1) - 1 - j] = RANDOM(mt_[0][channel], 2);
                x += R[l * (i + 1) - 1 - j];
            }
            Z[i * (1<<l) + x] = 1;
        }

        r = share_new_channel(n * l, 2, R, channel);
        z = share_new_channel(n * (1<<l), new_q, Z, channel);

        free(R);
        free(Z);
    }
    else {
        r = share_new_channel(n * l, 2, R, channel);
        z = share_new_channel(n * (1<<l), new_q, Z, channel);
    }

    NEWT(unitvb_correlated_randomness, cr);
    cr->n = n;
    cr->l = l;
    cr->new_q = new_q;
    cr->r = r;
    cr->z = z;
    cr->z_raw = NULL;

    return cr;
}

typedef struct UV_tables {
    int n;
    share_t old_q;
    share_t new_q;
    precomp_table r, z;
    MMAP *map;
}* UV_tables;

typedef struct uv_tbl_list {
    UV_tables tbl;
    int n;
    long count; // dshareを参考にして宣言してあるが，用途は不明
    struct uv_tbl_list *next;
}* uv_tbl_list;

uv_tbl_list PRE_UV_tbl[MAX_CHANNELS];
long PRE_UV_count[MAX_CHANNELS];

// 相関係数(correlated randomness)の前計算
// 位数old_qの長さnのベクトルx=(x_0, x_1, \ldots, x_{n-1})のシェアが与えられた時に，
// i=0, 1, \ldots, n-1に対して，x_i番目の要素が１であるold_q次元の単位ベクトルのシェアを返したい．単位ベクトルの各要素の位数はnew_qである．
// この関数ではそこで必要となる相関係数を前計算する．
// i=0, 1, \ldots, n-1に対して，位数old_qのランダムな整数r_iとr_i番目の単位ベクトルのシェアを前計算してファイルに書き込む．
void UV_tables_precomp(int n, share_t old_q, share_t new_q, char *fname) {
    // 前計算の結果を書き込むファイルの準備
    FILE *fp0;
    FILE *fp1;
    FILE *fp2;
    char *fname0 = precomp_fname(fname, 0);
    char *fname1 = precomp_fname(fname, 1);
    char *fname2 = precomp_fname(fname, 2);
    fp0 = fopen(fname0, "wb");
    fp1 = fopen(fname1, "wb");
    fp2 = fopen(fname2, "wb");
    if (fp0 == NULL) {
        printf("cannot open %s\n", fname0);
        exit(1);
    }  
    if (fp1 == NULL) {
        printf("cannot open %s\n", fname1);
        exit(1);
    }  
    if (fp2 == NULL) {
        printf("cannot open %s\n", fname2);
        exit(1);
    }

    writeuint(sizeof(int), n, fp1);
    writeuint(sizeof(int), n, fp2);
    writeuint(sizeof(share_t), old_q, fp1);
    writeuint(sizeof(share_t), old_q, fp2);
    writeuint(sizeof(share_t), new_q, fp1);
    writeuint(sizeof(share_t), new_q, fp2);

    // 前計算に使用する乱数のシードの準備
    //unsigned long init[5]={0x123, 0x234, 0x345, 0x456, 0};
    //MT m0 = MT_init_by_array(init, 5);
    //MT mt0 = mt_[0][0];

    packed_array r1, r2;
    packed_array z1, z2;
    int k_old_q = blog(old_q - 1) + 1;
    int k_new_q = blog(new_q - 1) + 1;
    r1 = pa_new(n, k_old_q);
    r2 = pa_new(n, k_old_q);
    z1 = pa_new(n*old_q, k_new_q);
    z2 = pa_new(n*old_q, k_new_q);
    for (int i = 0; i < n; ++i) {
        //share_t r = RANDOM(mt0, old_q);
        //share_t r = RANDOM(mt0, old_q);
        share_t r = RANDOM(mt0, old_q);
        share_t r_ = RANDOM(mt0, old_q);
        pa_set(r1, i, r_);
        pa_set(r2, i, (r + old_q - r_) % old_q);
        for (int j = 0; j < old_q; ++j) {
            share_t z_ = RANDOM(mt0, new_q);
            if (j == r) {
                share_t x = z_, y = (new_q +1 - z_) % new_q;
                pa_set(z1, i*old_q + j, x);
                pa_set(z2, i*old_q + j, y);
            }
            else {
                share_t x = z_, y = (new_q - z_) % new_q;
                pa_set(z1, i*old_q + j, x);
                pa_set(z2, i*old_q + j, y);
            }
        }
    }
    //precomp_write_share(fp1, r1);
    //precomp_write_share(fp2, r2);
    //precomp_write_share(fp1, z1);
    //precomp_write_share(fp2, z2);
    precomp_write_pa(fp1, r1, old_q);
    precomp_write_pa(fp2, r2, old_q);
    precomp_write_pa(fp1, z1, new_q);
    precomp_write_pa(fp2, z2, new_q);
    
    pa_free(r1);
    pa_free(r2);
    pa_free(z1);
    pa_free(z2);
    fclose(fp0);
    fclose(fp1);
    fclose(fp2);
    free(fname0);
    free(fname1);
    free(fname2);
    
    return;
}

void UV_tables_free(UV_tables tbl) {
    if (tbl == NULL)
        return;
    if (_party < 0 || _party > 2)
        return;
    precomp_free(tbl->r);
    precomp_free(tbl->z);
    if (tbl->map != NULL)
        mymunmap(tbl->map);
    free(tbl);
}

UV_tables UV_tables_read(char *fname) {
    NEWT(UV_tables, tbl);

    if (_party <= 0 || _party > 2) {
        tbl->r = tbl->z = NULL;
        tbl->map = NULL;
        return tbl;
    }

    char *fname2 = precomp_fname(fname, _party);

    MMAP *map = NULL;
    map = mymmap(fname2);
    uchar *p = (uchar *)map->addr;//printf("p: %p\n", p);
    tbl->n = getuint(p, 0, sizeof(int)); p += sizeof(int);//printf("p: %p\n", p);
    tbl->old_q = getuint(p, 0, sizeof(share_t)); p += sizeof(share_t);//printf("p: %p\n", p);
    tbl->new_q = getuint(p, 0, sizeof(share_t)); p += sizeof(share_t);//printf("p: %p\n", p);
    tbl->r = precomp_read(&p);
    tbl->z = precomp_read(&p);
    tbl->map = map;

    free(fname2);

    return tbl;
}

unitv_correlated_randomness unitv_cr_new_party0(int n, share_t old_q, share_t new_q) {
    NEWT(unitv_correlated_randomness, cr);
    cr->n = n;
    cr->old_q = old_q;
    cr->new_q = new_q;
    cr->r = share_const(n, 0, old_q);
    cr->z = share_const(n*old_q, 0, new_q);
    NEWA(cr->z_raw, share_t, n*old_q);
    memset(cr->z_raw, 0, sizeof(share_t)*n*old_q);
    for (int i = 0; i < n; ++i) {
      share_setpublic(cr->z, i*old_q, 1);
      cr->z_raw[i*old_q] = 1;
    }
    return cr;
}

// 事前計算の表から取ってくる
// nはデータのシェア配列の長さ．n <= tbl->nであれば良い．
static void unitv_new_precomp(UV_tables tbl, int n, share_t old_q, share_t new_q, unitv_correlated_randomness *cr_) {
    if (_party > 2)
        return;
    PRE_UV_count[0] += 1;   // ???
    if (_party <= 0) {
        *cr_ = unitv_cr_new_party0(n, old_q, new_q);
        return;
    }

    NEWT(unitv_correlated_randomness, cr);
    cr->n = n;
    cr->old_q = old_q;//printf("old_q %d\n", cr->old_q);fflush(stdout);
    cr->new_q = new_q;//printf("new_q %d\n", cr->new_q);fflush(stdout);
    cr->r = share_const(n, 0, cr->old_q);
    // printf("r ");
    pa_iter itr = pa_iter_new(cr->r->A);
    for (int i = 0; i < n; ++i) {
        //pa_set(cr->r->A, i, precomp_get(tbl->r) % cr->old_q);
        pa_iter_set(itr, precomp_get(tbl->r) % cr->old_q);
        // printf("%d ", (int)pa_get(cr->r->A, i));
    }
    pa_iter_flush(itr);
    // printf("\n");fflush(stdout);
    cr->z = share_const(n*cr->old_q, 0, cr->new_q);
    NEWA(cr->z_raw, share_t, n*cr->old_q);
    itr = pa_iter_new(cr->z->A);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < cr->old_q; ++j) {
            //pa_set(cr->z->A, i*cr->old_q+j, precomp_get(tbl->z) % cr->new_q);
            share_t x = precomp_get(tbl->z) % cr->new_q;
            pa_iter_set(itr, x);
            cr->z_raw[i*cr->old_q+j] = x;
        }
    }
    pa_iter_flush(itr);

    *cr_ = cr;
    return;
}

uv_tbl_list uv_tbl_list_insert(UV_tables tbl, int n, int old_q, int new_q, uv_tbl_list head) {
    NEWT(uv_tbl_list, list);
    list->tbl = tbl;
    list->tbl->n = n;
    list->tbl->old_q = old_q;
    list->tbl->new_q = new_q;
    list->n = n;
    list->count = 0;
    list->next = head;
    return list;
}

// 長さn，位数old_qから位数new_qへと変換するためのcorrelated randomnessを返す
UV_tables uv_tbl_list_search(uv_tbl_list list, int n, share_t old_q, share_t new_q) {
    while (list != NULL) {
        if (list->tbl->n == n && list->tbl->old_q == old_q && list->tbl->new_q == new_q) {
            return list->tbl;
        }
        list = list->next;
    }
    return NULL;
}

// 長さn以上，位数old_qから位数new_qへと変換するためのcorrelated randomnessを返す
UV_tables uv_tbl_list_search2(uv_tbl_list list, int n, share_t old_q, share_t new_q) {
    while (list != NULL) {
        if (/*list->tbl->n >= n &&*/ list->tbl->old_q == old_q && list->tbl->new_q % new_q == 0) {
            return list->tbl;
        }
        list = list->next;
    }
    return NULL;
}

void uv_tbl_list_free(uv_tbl_list list) {
    uv_tbl_list next;
    while (list != NULL) {
        next = list->next;
        UV_tables_free(list->tbl);
        free(list);
        list = next;
    }
}

void uv_tbl_init(void) {
    for (int i = 0; i < _opt.channels; ++i) {
        PRE_UV_tbl[i] = NULL;
        PRE_UV_count[i] = 0;
    }
}

void uv_tbl_read(int channel, int n, int old_q, int new_q, char *fname) {
    UV_tables tbl = UV_tables_read(fname);
    PRE_UV_tbl[channel] = uv_tbl_list_insert(tbl, n, old_q, new_q, PRE_UV_tbl[channel]);
}

share_array* Unitv_channel(share_array x, share_t new_q, int channel) {
    if (_party > 2)
        return NULL;
    
    int n = x->n, old_q = x->q;
    // printf("x: ");share_print(x);

    // 相関乱数の用意
    unitv_correlated_randomness cr;
    UV_tables tbl = uv_tbl_list_search2(PRE_UV_tbl[channel], x->n, old_q, new_q);//printf("search ok\n");fflush(stdout);
    if (tbl != NULL) {  // 条件に合致する前計算テーブルが存在する時
      // printf("UV_tables n = %d old_q = %d new_q = %d\n", tbl->n, tbl->old_q, tbl->new_q);
      // printf("UV_tables n = %d old_q = %d new_q = %d\n", tbl->n, tbl->old_q, tbl->new_q);
      // printf("before unitv_new_precomp\n");   fflush(stdout);
      unitv_new_precomp(tbl, x->n, old_q, new_q, &cr);
      // printf("unitv_new_precomp ok\n");fflush(stdout);
    } else {
      if (_opt.warn_precomp) {
        printf("without UV_table n = %d old_q = %d new_q = %d\n", x->n, x->q, new_q);fflush(stdout);
      }
      cr = Unitv_prep_channel(x->n, x->q, new_q, channel);
    }

    // 答えの計算
    share_array *ans;
    NEWA(ans, share_array, n);
    share_array s = vsub(cr->r, x);
    // share_array r_re = share_reconstruct(cr->r);
    //share_array s_reconstructed = share_reconstruct(s);//printf("share_reconstruct ok\n");fflush(stdout);
    share_array s_reconstructed = share_reconstruct_channel(s, channel);// !!!!!
    // share_array z_re = share_reconstruct(cr->z);
    for (int i = 0; i < x->n; ++i) {
      share_t m = pa_get(s_reconstructed->A, i);
      // printf("r: %d\n", (int)pa_get(r_re->A, i));
      // printf("s: %d\n", m);
      ans[i] = share_const(old_q, 0, new_q);
#if 0
      // printf("z ");
      for (int j = 0; j < old_q; ++j) {
        u64 a = pa_get(cr->z->A, old_q*i+(j+m) % old_q);
        // share_t y = pa_get(z_re->A, old_q*i+j);
        // printf("%d ", y);
        pa_set(ans[i]->A, j, a);
      }
#else
      share_t *cr_tmp = pa_unpack(cr->z->A);
      pa_iter itr = pa_iter_new(ans[i]->A);
      for (int j = 0; j < old_q; ++j) {
        if (cr_tmp[old_q*i+(j+m) % old_q] != cr->z_raw[old_q*i+(j+m) % old_q]) {
          printf("%d %d\n", cr_tmp[old_q*i+(j+m) % old_q], cr->z_raw[old_q*i+(j+m) % old_q]);
        }
        pa_iter_set(itr, cr_tmp[old_q*i+(j+m) % old_q]);
      }
      pa_iter_flush(itr);
      free(cr_tmp);
#endif
      // printf("\n");
    }
    _free(s);
    _free(s_reconstructed);
    unitv_cr_free(cr);

    return ans;
}
#define Unitv(x, new_q) Unitv_channel(x, new_q, 0)

share_array* Unitvb_channel(int n, share_array *x, share_t new_q, int channel) {
    if (_party > 2)
        return NULL;

    if (order(x[0]) != 2) {
        printf("Unitvb order(x[0]) = %d\n", order(x[0]));
        exit(1);
    }

    int l = len(x[0]);
    
    // 相関係数の生成
    unitvb_correlated_randomness cr = Unitvb_prep_channel(n, l, new_q, channel);

    // 答えの計算
    share_array serialized_p = share_const(n * l, 0, 2);
    // NEWA(p, share_array, n);
    for (int i = 0; i < n; ++i) {
        share_setshares(serialized_p, i * l, (i + 1) * l, x[i], 0);
    }
    vadd_(serialized_p, cr->r);
    share_array serialized_p_re = _reconstruct_channel(serialized_p, channel);

    share_array *ans;
    NEWA(ans, share_array, n);
    for (int i = 0; i < n; ++i) {
        ans[i] = share_const(1<<l, 0, new_q);
        share_array p_re = _slice(serialized_p_re, i * l, (i + 1) * l);
        share_t p = 0;
        for (int j = 0; j < l; ++j) {
            p <<= 1;
            p += share_getraw(p_re, l - 1 - j);
        }
        for (int j = 0; j < 1<<l; ++j) {
            share_t id = j ^ p;
            share_t x = share_getraw(cr->z, i * (1<<l) + id);
            share_setraw(ans[i], j, x);
        }

        share_free(p_re);
    }

    unitvb_cr_free(cr);
    share_free(serialized_p);
    share_free(serialized_p_re);

    return ans;
}

_ UnitvB_channel(_bits x, share_t new_q, int channel) 
{
  if (_party > 2) return NULL;

  if (order_bits(x) != 2) {
    printf("UnitvB order(x[0]) = %d\n", order_bits(x));
    exit(1);
  }

  int n = len_bits(x);
  int l = depth_bits(x);
  int m = 1<<l;
    
  // 相関係数の生成
  unitvb_correlated_randomness cr = Unitvb_prep_channel(n, l, new_q, channel);

  // 答えの計算
  _ serialized_p = share_const(n * l, 0, 2);
  // NEWA(p, share_array, n);
  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < l; j++) {
      share_setshare(serialized_p, i * l + j, x->a[j], i); // 連続する l ビットが1つの値 x_i を表す
    }
  }
  vadd_(serialized_p, cr->r);
  _ serialized_p_re = _reconstruct_channel(serialized_p, channel);

  _ ans = share_const(m*n, 0, new_q);

  for (int i = 0; i < n; ++i) {
    share_t p = 0;
    for (int j = 0; j < l; ++j) {
      p <<= 1;
      p += share_getraw(serialized_p_re, i * l+ (l - 1 - j));
    }
    for (int j = 0; j < m; ++j) {
      share_t id = j ^ p;
      share_t x = share_getraw(cr->z, i * m + id);
      share_setraw(ans, i * m + j, x);
    }
  }

  unitvb_cr_free(cr);
  share_free(serialized_p);
  share_free(serialized_p_re);

  return ans;
}



share_array** ParallelUnitv_channel(int l, share_array *x, int *new_q, int channel) {
    if (_party > 2)
        return NULL;
    
    int *n, *old_q;
    NEWA(n, int, l);
    NEWA(old_q, int, l);
    for (int i = 0; i < l; ++i) {
        n[i] = len(x[i]);
        //printf("n[%d] = %d\n", i, n[i]);
        old_q[i] = order(x[i]);
    }

    unitv_correlated_randomness *cr;
    UV_tables tbl;
    NEWA(cr, unitv_correlated_randomness, l);
    // NEWA(tbl, UV_tables, l);
    for (int i = 0; i < l; ++i) {
        tbl = uv_tbl_list_search2(PRE_UV_tbl[channel], n[i], old_q[i], new_q[i]);

        if (tbl != NULL) {
            //printf("with UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            unitv_new_precomp(tbl, n[i], old_q[i], new_q[i], cr + i);
        }
        else {
            if (_opt.warn_precomp) {
                printf("without UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            }
            cr[i] = Unitv_prep_channel(n[i], old_q[i], new_q[i], channel);
        }
    }

    share_array **ans;
    //share_array *ans2;
    NEWA(ans, share_array*, l);
    //NEWA(ans2, share_array, l);
    share_array *s;
    share_array *s_r;
    NEWA(s, share_array, l);
    NEWA(s_r, share_array, l);

    // parallel reconstruct
    // TODO: チェック
    if (_party == 0){
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            s_r[i] = share_const(len(s[i]), 0, order(s[i]));
            share_setshares(s_r[i], 0, len(s[i]), s[i], 0);
        }
    }
    else if (_party == 1 || _party == 2) {
      if (_opt.send_queue == 1) {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            mpc_send_queue_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
        mpc_send_flush_channel(TO_PAIR, channel);
      } else {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            // printf("s[i]:   ");share_print(s[i]);fflush(stdout);
            mpc_send_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
      }
      for (int i = 0; i < l; ++i) {
        s_r[i] = share_const(len(s[i]), 0, order(s[i]));
        mpc_recv_channel(FROM_PAIR, s_r[i]->A->B, pa_size(s_r[i]->A), channel);
        vadd_(s_r[i], s[i]);
      }
    }
    
    for (int i = 0; i < l; ++i) {
        NEWA(ans[i], share_array, n[i]);
        for (int j = 0; j < n[i]; ++j) {
            share_t m = share_getraw(s_r[i], j);
            ans[i][j] = share_const(old_q[i], 0, new_q[i]); // ここがやたら多い
            //ans2[i] = share_const(n[i]*old_q[i], 0, new_q[i]);
            //printf("share_const i=%d ni=%d len=%d q=%d\n", i, n[i], old_q[i], new_q[i]);
            pa_iter itr_ans = pa_iter_new(ans[i][j]->A);
            //pa_iter_new(ans2[i]->A);
            for (int k = 0; k < old_q[i]; ++k) {
                share_t a = share_getraw(cr[i]->z, old_q[i] * j + (k + m) % old_q[i]);
                //share_iter_setraw(ans[i][j], a);
                pa_iter_set(itr_ans, a);
            }
            //share_iter_setraw_flush(ans[i][j]);
            pa_iter_flush(itr_ans);
        }
        //share_iter_setraw_flush(ans2[i]);
        
        share_free(s[i]);
        share_free(s_r[i]);
        unitv_cr_free(cr[i]);
    }
    // printf("ParallelUnitvOK\n");fflush(stdout);
    free(n);    free(cr);   free(s);    free(s_r);
    free(old_q);
    return ans;
}

share_array* ParallelUnitv2_channel(int l, share_array *x, int *new_q, int channel) {
    if (_party > 2)
        return NULL;
    
    int *n, *old_q;
    NEWA(n, int, l);
    NEWA(old_q, int, l);
    for (int i = 0; i < l; ++i) {
        n[i] = len(x[i]);
        old_q[i] = order(x[i]);
    }

    unitv_correlated_randomness *cr;
    UV_tables tbl;
    NEWA(cr, unitv_correlated_randomness, l);
    // NEWA(tbl, UV_tables, l);
    for (int i = 0; i < l; ++i) {
        tbl = uv_tbl_list_search2(PRE_UV_tbl[channel], n[i], old_q[i], new_q[i]);

        if (tbl != NULL) {
            //printf("with UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            unitv_new_precomp(tbl, n[i], old_q[i], new_q[i], cr + i);
        }
        else {
            if (_opt.warn_precomp) {
                printf("without UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            }
            cr[i] = Unitv_prep_channel(n[i], old_q[i], new_q[i], channel);
        }
    }

    share_array **ans;
    share_array *ans2;
    //NEWA(ans, share_array*, l);
    NEWA(ans2, share_array, l);
    share_array *s;
    share_array *s_r;
    NEWA(s, share_array, l);
    NEWA(s_r, share_array, l);

    // parallel reconstruct
    // TODO: チェック
    //if (_party == 0){
    if (_party <= 0){
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            s_r[i] = share_const(len(s[i]), 0, order(s[i]));
            share_setshares(s_r[i], 0, len(s[i]), s[i], 0);
        }
    }
    else if (_party == 1 || _party == 2) {
      if (_opt.send_queue) {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            mpc_send_queue_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
        mpc_send_flush_channel(TO_PAIR, channel);        
      } else {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            // printf("s[i]:   ");share_print(s[i]);fflush(stdout);
            mpc_send_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
      }
      for (int i = 0; i < l; ++i) {
        s_r[i] = share_const(s[i]->n, 0, s[i]->q);
        mpc_recv_channel(FROM_PAIR, s_r[i]->A->B, pa_size(s_r[i]->A), channel);
        vadd_(s_r[i], s[i]);
      }
    }
    
    for (int i = 0; i < l; ++i) {
        //NEWA(ans[i], share_array, n[i]);
        ans2[i] = share_const(n[i]*old_q[i], 0, new_q[i]);
        pa_iter itr_ans2 = pa_iter_new(ans2[i]->A);
        for (int j = 0; j < n[i]; ++j) {
            share_t m = share_getraw(s_r[i], j);
            //ans[i][j] = share_const(old_q[i], 0, new_q[i]); // ここがやたら多い
            //printf("share_const n=%d q=%d\n", old_q[i], new_q[i]);
            for (int k = 0; k < old_q[i]; ++k) {
                share_t a = share_getraw(cr[i]->z, old_q[i] * j + (k + m) % old_q[i]);
                //share_iter_setraw(ans2[i], a);
                pa_iter_set(itr_ans2, a);
            }
        }
        //share_iter_setraw_flush(ans2[i]);
        pa_iter_flush(itr_ans2);
        
        share_free(s[i]);
        share_free(s_r[i]);
        unitv_cr_free(cr[i]);
    }
    // printf("ParallelUnitvOK\n");fflush(stdout);
    free(n);    free(cr);   free(s);    free(s_r);
    free(old_q);
    return ans2;
}

#if 1
share_array ParallelUnitv3_channel(int l, share_array *x, int *new_q, int channel) {
    if (_party > 2)
        return NULL;
    
    int *n, *old_q;
    NEWA(n, int, l);
    NEWA(old_q, int, l);
    for (int i = 0; i < l; ++i) {
        n[i] = len(x[i]);
        old_q[i] = order(x[i]);
    }

    unitv_correlated_randomness *cr;
    UV_tables tbl;
    NEWA(cr, unitv_correlated_randomness, l);
    // NEWA(tbl, UV_tables, l);
    for (int i = 0; i < l; ++i) {
        tbl = uv_tbl_list_search2(PRE_UV_tbl[channel], n[i], old_q[i], new_q[i]);

        if (tbl != NULL) {
            //printf("with UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            unitv_new_precomp(tbl, n[i], old_q[i], new_q[i], cr + i);
        }
        else {
            if (_opt.warn_precomp) {
                printf("without UV_table n = %d old_q = %d new_q = %d\n", x[i]->n, x[i]->q, new_q[i]);fflush(stdout);
            }
            cr[i] = Unitv_prep_channel(n[i], old_q[i], new_q[i], channel);
        }
    }

    //share_array **ans;
    //share_array *ans2;
    share_array ans3;
    //NEWA(ans, share_array*, l);
    //NEWA(ans2, share_array, l);
    share_array *s;
    share_array *s_r;
    NEWA(s, share_array, l);
    NEWA(s_r, share_array, l);

    // parallel reconstruct
    // TODO: チェック
    if (_party == 0){
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            s_r[i] = share_const(len(s[i]), 0, order(s[i]));
            share_setshares(s_r[i], 0, len(s[i]), s[i], 0);
        }
    }
    else if (_party == 1 || _party == 2) {
      if (_opt.send_queue) {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            mpc_send_queue_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
        mpc_send_flush_channel(TO_PAIR, channel);
      } else {
        for (int i = 0; i < l; ++i) {
            s[i] = vsub(cr[i]->r, x[i]);
            // printf("cr[i]->r: ");share_print(cr[i]->r);
            // printf("x[i]:   ");share_print(x[i]);fflush(stdout);
            // printf("s[i]:   ");share_print(s[i]);fflush(stdout);
            mpc_send_channel(TO_PAIR, s[i]->A->B, pa_size(s[i]->A), channel);
        }
      }
      for (int i = 0; i < l; ++i) {
        s_r[i] = share_const(s[i]->n, 0, s[i]->q);
        mpc_recv_channel(FROM_PAIR, s_r[i]->A->B, pa_size(s_r[i]->A), channel);
        vadd_(s_r[i], s[i]);
      }
    }
    
    ans3 = share_const(l*n[0], 0, new_q[0]);
    // pa_iter_new(ans3->A);
    pa_iter itr_ans3 = pa_iter_new(ans3->A);
    for (int i = 0; i < l; ++i) {
        //NEWA(ans[i], share_array, n[i]);
        //ans2[i] = share_const(n[i]*old_q[i], 0, new_q[i]);
        for (int j = 0; j < n[i]; ++j) {
            share_t m = share_getraw(s_r[i], j);
            //ans[i][j] = share_const(old_q[i], 0, new_q[i]); // ここがやたら多い
            //printf("share_const n=%d q=%d\n", old_q[i], new_q[i]);
            //pa_iter_new(ans[i][j]->A);
            //pa_iter_new(ans2[i]->A);
            for (int k = 0; k < old_q[i]*0+1; ++k) {
                share_t a = share_getraw(cr[i]->z, old_q[i] * j + (k + m) % old_q[i]);
                //pa_iter_set(ans3->A, share_getraw(cr[i]->z, old_q[i] * j + (k + m) % old_q[i]));
                pa_iter_set(itr_ans3, share_getraw(cr[i]->z, old_q[i] * j + (k + m) % old_q[i]));
            }
            //share_iter_setraw_flush(ans[i][j]);
        }
        //share_iter_setraw_flush(ans2[i]);
        
        share_free(s[i]);
        share_free(s_r[i]);
        unitv_cr_free(cr[i]);
    }
    //pa_iter_flush(ans3->A);
    pa_iter_flush(itr_ans3);
    // printf("ParallelUnitvOK\n");fflush(stdout);
    free(n);    free(cr);   free(s);    free(s_r);
    free(old_q);
    return ans3;
}
#endif

typedef struct Partition {
    int l;  // the input (share_array) bit-length
    int m;  // the length of del
    int *del;   // sum of del[i] is l
}* Partition;

void FreePartition(Partition par) {
    free(par->del);
    free(par);
}

//////////////////////////////////////////////////////////
// x の2進表記を p に従って分割する
//////////////////////////////////////////////////////////
share_t* Expand(share_t x, share_t q, Partition p) {
    if (blog(q - 1) + 1 != p->l) {
        printf("Expand q: %d p->l: %d\n", q, p->l);
        exit(1);
    }
    if (1<<blog(q - 1) + 1 != q) {
        printf("Expand q: %d\n", q);
        exit(1);
    }

    share_t *ans;
    NEWA(ans, share_t, p->m);
    int s = 0;
    for (int i = 0; i < p->m; ++i) {
        int mask = (1<<p->del[i]) - 1;
        ans[i] = (x >> s) & mask;
        
        s += p->del[i];
    }

    return ans;
}

// 3bitsごとに分割する
Partition MakeOverflowPatition1(int l) {
    NEWT(Partition, par);
    par->l = l;
    par->m = (l + 3 - 1) / 3;   // 3で切り上げ
    NEWA(par->del, int, par->m);
    for (int i = 0; i < par->m; ++i) {
        if (i < par->m - 1) {
            par->del[i] = 3;
        }
        else {
            if (l % 3 == 0) {
                par->del[i] = 3;
            }
            else {
                par->del[i] = l % 3;
            }
        }
    }

    return par;
}

Partition MakeOverflowPatition2(int m) {
    NEWT(Partition, T);
    T->m = m - 1;
    T->l = m;
    NEWA(T->del, int, T->m);
    for (int i = 0; i < T->m - 1; ++i) {
        T->del[i] = 1;
    }
    T->del[T->m - 1] = 2;

    return T;
}

Partition MakeOverflowPatition3(int m) {
    NEWT(Partition, T);
    T->m = m;
    T->l = m;
    NEWA(T->del, int, T->m);
    for (int i = 0; i < T->m; ++i) {
        T->del[i] = 1;
    }
    //T->del[T->m - 1] = 2;

    return T;
}

int CalcParamInOverflow2(Partition T) {
#if 0
    //printf("CalcParamInOverflow2\n");
    int tk = -1;
    for (int i=0; i<T->m; i++) {
      tk += T->del[i];
      printf("T[%d] = %d tk = %d\n", i, T->del[i], tk);
      printf("N >= %d\n", (1<<T->del[i]-1)*(T->m-tk+1));
    }
#endif
    int N = T->m + 2; // 元の桁数 + 1
    N = 1 << (blog(N - 1) + 1); // N 以上の最小の2のべき乗
    return N;
}

int CalcParamInOverflow3(Partition T) {
    //printf("CalcParamInOverflow3\n");
    int N = T->m + 2; // 適当
    //int N = 64; // 適当
    N = 1 << (blog(N - 1) + 1); // N 以上の最小の2のべき乗
    return N;
}

share_pair OverflowConst1_channel(share_array x, share_t new_q, int channel) {
    share_t old_q = order(x);
    int n = len(x);
    if (old_q != 1 << (blog(old_q - 1) + 1)) {
        printf("ShortOverflowConst_channel: old_q = %d\n", old_q);
        exit(1);
    }

    share_array z = share_const(n, 0, 2 * old_q);
    for (int i = 0; i < n; ++i) {
        share_setraw(z, i, share_getraw(x, i));
    }

    share_array *v = Unitv_channel(z, new_q, channel);
    // printf("z: ");  share_print(z);
    share_free(z);
    share_array b = share_const(n, 0, new_q);
    share_array c = share_const(n, 0, new_q);
    for (int i = 0; i < n; ++i) {
        // share_print(v[i]);
        // share_array v_r = share_reconstruct(v[i]);
        // share_print(v_r);
        share_t r = share_getraw(v[i], old_q - 1);
        share_setraw(b, i, r);
        //for (int j = old_q; j < 2 * old_q; ++j) {
        for (int j = old_q/2; j < old_q; ++j) {
            // share_t r = share_getraw(v[i], j);
            // share_addpublic(c, i, r);
            share_addshare(c, i, v[i], j);
        }
        share_free(v[i]);
    }

    free(v);
    
    return (share_pair){b, c};
}

share_pair* ParallelOverflowConst1_channel(int m, share_array *x, share_t *new_q, int channel) {
    share_t *old_q;
    int *n;
    NEWA(old_q, share_t, m);
    NEWA(n, int, m);
    for (int i = 0; i < m; ++i) {
        old_q[i] = order(x[i]);
        n[i] = len(x[i]);
        if (old_q[i] != 1<< (blog(old_q[i] - 1) + 1)) {
            printf("ParallelOverflowConst1_channel: old_q[%d] = %d\n", i, old_q[i]);
            exit(1);
        }
    }

    share_array *z;
    NEWA(z, share_array, m);
    for (int i = 0; i < m; ++i) {
        z[i] = share_const(n[i], 0, 2 * old_q[i]);
        for (int j = 0; j < n[i]; ++j) {
            share_setraw(z[i], j, share_getraw(x[i], j));
        }
    }

    share_t Z = order(z[0]);
    //share_array **v = ParallelUnitv_channel(m, z, new_q, channel);
    share_array *v2 = ParallelUnitv2_channel(m, z, new_q, channel);
#if 0
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n[i]; ++j) {
            printf("v[%d][%d] ", i, j); _print_debug(v[i][j]);
        }
        printf("v2[%d] ", i); _print_debug(v2[i]);
    }
#endif
    for (int i = 0; i < m; ++i) {
        share_free(z[i]);
    }
    free(z);

    share_array *b, *c;
    NEWA(b, share_array, m);
    NEWA(c, share_array, m);
    for (int i = 0; i < m; ++i) {
        //printf("old_q[%d] = %d new_q[%d] = %d\n", i, old_q[i], i, new_q[i]);
        b[i] = share_const(n[i], 0, new_q[i]);
        c[i] = share_const(n[i], 0, new_q[i]);
        for (int j = 0; j < n[i]; ++j) {
            //printf("i %d j %d v ", i, j); _print(v[i][j]); _print_debug(v[i][j]);
            //share_t r = share_getraw(v[i][j], old_q[i] - 1);
            share_t r = share_getraw(v2[i], Z * j + old_q[i] - 1);
            share_setraw(b[i], j, r);
            for (int k = old_q[i]; k < 2 * old_q[i]; ++k) {
                // share_t r = share_getraw(v[i][j], k);
                //share_addshare(c[i], j, v[i][j], k);
                share_addshare(c[i], j, v2[i], Z*j + k);
            }
            //share_free(v[i][j]);
        }
        //printf("i %d b ", i); _print(b[i]); _print_debug(b[i]);
        //printf("i %d c ", i); _print(c[i]); _print_debug(c[i]);
        //free(v[i]);
        _free(v2[i]);
    }

    free(n);
    free(old_q);
    //free(v);
    free(v2);

    share_pair *ans;
    NEWA(ans, share_pair, m);
    for (int i = 0; i < m; ++i) {
        ans[i].x = b[i];
        ans[i].y = c[i];
    }

    free(b);    free(c);

    return ans;
}


// 出力の位数は2
share_array OverflowConst2_channel(share_array y, int channel) {
    // int l = order(y);
    int n = len(y);
    share_t old_q = order(y);
    int l = blog(old_q - 1) + 1;    // TODO: lが短い時はOverflowConst1_channelを発動するように変更を加える．
    //Partition par = MakeOverflowPatition2(l);
    //Partition par = MakeOverflowPatition2(l);
    //Partition T = MakeOverflowPatition2(par->m);
    Partition par = MakeOverflowPatition3(l);
    Partition T = MakeOverflowPatition3(par->m);
    //Partition T = MakeOverflowPatition2(l); // test

    share_t **partitioned_y_raw;
    NEWA(partitioned_y_raw, share_t*, n);
    for (int i = 0; i < n; ++i) {
        partitioned_y_raw[i] = Expand(share_getraw(y, i), old_q, par);
    }

    //share_t N = CalcParamInOverflow2(T);
    share_t N = CalcParamInOverflow3(T);
    share_t *mid_q;
    NEWA(mid_q, share_t, par->m);
    for (int i = 0; i < par->m; ++i) {
        mid_q[i] = N;
    }
    //mid_q[par->m - 1] = N*2; // test

    share_array *partitioned_y;
    NEWA(partitioned_y, share_array, par->m);
    for (int i = 0; i < par->m; ++i) {
        partitioned_y[i] = share_const(n, 0, 1<<par->del[i]);
        for (int j = 0; j < n; ++j) {
            share_setraw(partitioned_y[i], j, partitioned_y_raw[j][i]);
        }
        //printf("partitioned_y %d ", i); _print(partitioned_y[i]); _print_debug(partitioned_y[i]);
    }
    for (int i = 0; i < n; ++i) {
        free(partitioned_y_raw[i]);
    }
    free(partitioned_y_raw);

    share_pair *pr = ParallelOverflowConst1_channel(par->m, partitioned_y, mid_q, channel);

    for (int i = 0; i < par->m; ++i) {
        share_free(partitioned_y[i]);
    }
    free(partitioned_y);
    // printf("ParallelOverflowConst1_channel completed\n");fflush(stdout);
    free(mid_q);

    share_array *z;
    NEWA(z, share_array, T->m);
    int *t;
    NEWA(t, int, T->m);
    NEWA(mid_q, share_t, T->m);
    t[0] = 0;
    for (int k = 0; k < T->m; ++k) {
        mid_q[k] = 2;
        if (k == 0) {
            t[k] = T->del[k] - 1;
        }
        else {
            t[k] = T->del[k] + t[k-1];
        }
        z[k] = share_const(n, 0, N);
        for (int i = 0; i < n; ++i) {
            share_t r = 0;
            for (int j = 0; j < T->del[k]; ++j) {
                //printf("i=%d j=%d t[%d] - %d + 1 = %d\nt[%d] - %d = %d\n", i, j, k, j, t[k] - j + 1,  k, j, t[k] - j);fflush(stdout);
                if (t[k] - j + 1 >= par->m) {
                    r = (r + (1 << (T->del[k] - 1 - j)) * share_getraw(pr[t[k] - j].y, i)) % N;
                    //printf("%d * y[%d] ", (1 << (T->del[k] - 1 - j)), t[k] - j); _print(pr[t[k] - j].y); _print_debug(pr[t[k] - j].y);
                }
                else {
                    r = (r + (1 << (T->del[k] - 1 - j)) * (share_getraw(pr[t[k] - j + 1].x, i) + share_getraw(pr[t[k] - j].y, i))) % N;
                    //printf("%d * y[%d] ", (1 << (T->del[k] - 1 - j)), t[k] - j); _print(pr[t[k] - j].y); _print_debug(pr[t[k] - j].y);
                    //printf("%d * x[%d] ", (1 << (T->del[k] - 1 - j)), t[k] - j+1); _print(pr[t[k] - j+1].x); _print_debug(pr[t[k] - j+1].x);
                }
            }
            for (int j = t[k]+2; j < par->m; ++j) {
                // printf("j: %d\n", j);
                r = (r + (1 << (T->del[k] - 1)) * share_getraw(pr[j].x, i)) % N;
                //printf("%d * x[%d] ", (1 << (T->del[k] - 1)), j); _print(pr[j].x); _print_debug(pr[j].x);
            }
            //printf("r %d\n", r);
            share_setraw(z[k], i, r);
        }
        //printf("z[%d] ", k); _print(z[k]); _print_debug(z[k]);
    }

    //share_array **f = ParallelUnitv_channel(T->m, z, mid_q, channel);
    share_array *f2 = ParallelUnitv2_channel(T->m, z, mid_q, channel);
#if 0
    for (int k = 0; k < T->m; ++k) {
        for (int i = 0; i < n; ++i) {
            printf("f[%d][%d]", k, i); _print_debug(f[k][i]);
        }
        printf("f2[%d]", k); _print_debug(f2[k]);
    }
#endif
    for (int k = 0; k < T->m; ++k) {
        share_free(z[k]);
    }
    free(z);
    free(mid_q);

    share_array *g, of = share_const(n, 0, 2);
    NEWA(g, share_array, T->m);
    for (int k = 0; k < T->m; ++k) {
        g[k] = share_const(n, 0, 2);
#if 0
        for (int i = 0; i < n; ++i) {
            //printf("f[%d][%d] ", k, i); _print_debug(f[k][i]);
            for (int j = (1 << (T->del[k] - 1)) * (par->m - t[k]); j < N; ++j) {
                //share_addshare(g[k], i, f[k][i], j);
                share_addshare(g[k], i, f2[k], i*N + j);
            }
        }   
#else
        pa_iter itr_g = pa_iter_new(g[k]->A);
        share_t q = order(g[k]);
        int js = (1 << (T->del[k] - 1)) * (par->m - t[k]);
        for (int i = 0; i < n; ++i) {
          pa_iter itr_f = pa_iter_pos_new(f2[k]->A, i*N + js);
          share_t z = 0;
          for (int j = js; j < N; ++j) {
            z += pa_iter_get(itr_f);
          }
          pa_iter_set(itr_g, z % q);
          pa_iter_free(itr_f);
        }
        pa_iter_flush(itr_g);
#endif
    }

    for (int i = 0; i < n; ++i) {
        //printf("g[%d] ", i); _print_debug(g[i]);
        for (int k = 0; k < T->m; ++k) {
            share_addshare(of, i, g[k], i);
            //share_free(f[k][i]);
        }
    }

    for (int k = 0; k < par->m; ++k) {
        share_free(pr[k].x);
        share_free(pr[k].y);
    }

    for (int k = 0; k < T->m; ++k) {
        share_free(g[k]);
        //free(f[k]);
        _free(f2[k]);
    }
    free(pr);
    FreePartition(par);
    FreePartition(T);
    free(t);
    //free(f);
    free(f2);
    free(g);

    return of;
}

// TODO: 入力長が大きいシェアの配列を複数一括で処理する関数の実装
//      Comparison2の実装に使用する
share_array* ParallelOverflow2_channel(int m, share_array *x, int channel);

// 1bitsごとに分割する
Partition MakeEqualityPatition(int l) {
    NEWT(Partition, par);
    par->l = l;
    par->m = l - 1;
    NEWA(par->del, int, par->m);
    for (int i = 0; i < par->m - 1; ++i) {
        par->del[i] = 1;
    }
    par->del[par->m - 1] = 2;

    return par;
}

Partition MakeEqualityPatition3(int l) {
    NEWT(Partition, par);
    par->l = l;
    par->m = l;
    NEWA(par->del, int, par->m);
    for (int i = 0; i < par->m; ++i) {
        par->del[i] = 1;
    }
    //par->del[par->m - 1] = 2;

    return par;
}

void Partition_free(Partition par)
{
  free(par->del);
  free(par);
}

share_array EqualityConst1_channel(share_array x, share_array y, share_t new_q, int channel) {
    if (_party > 2) {
        return NULL;
    }
    if (len(x) != len(y)) {
        printf("EqualityConst_channel len(x): %d    len(y): %d\n", len(x), len(y));
        exit(1);
    }
    if (order(x) != order(y)) {
        printf("EqualityConst_channel order(x): %d    order(y): %d\n", order(x), order(y));
        exit(1);
    }
    if (order(x) != 1<<(blog(order(x) - 1) + 1)) {
        printf("EqualityConst_channel order(x): %d\n", order(x));
        exit(1);
    }

    int n = len(x);
    share_t old_q = order(x);
    share_array d = vsub(x, y);
    share_array *e = Unitv_channel(d, new_q, channel);
    share_array ans = share_const(n, 0, new_q);
    for (int i = 0; i < n; ++i) {
        share_setshare(ans, i, e[i], 0);
        share_free(e[i]);
    }

    share_free(d);
    free(e);

    return ans;
}

share_array *ParallelEqualityConst1_channel(int m, share_array *x, share_array *y, share_t *new_q, int channel) {
    share_array *d;
    NEWA(d, share_array, m);
    for (int i = 0; i < m; ++i) {
        d[i] = vsub(x[i], y[i]);
    }

    //share_array **e = ParallelUnitv_channel(m, d, new_q, channel);
    //share_array *e2 = ParallelUnitv2_channel(m, d, new_q, channel);
    share_array e3 = ParallelUnitv3_channel(m, d, new_q, channel);
    share_array *ans;
    NEWA(ans, share_array, m);
    int idx = 0;
    for (int i = 0; i < m; ++i) {
        _free(d[i]);
        ans[i] = share_const(len(x[i]), 0, new_q[i]);
        for (int j = 0; j < len(x[i]); ++j) {
            //share_setshare(ans[i], j, e[i][j], 0);
            //printf("i %d j %d e %d %d\n", i, j, share_getraw(e[i][j], 0), share_getraw(e3, i*len(x[i])+j));
            //share_setshare(ans[i], j, e3, i*order(x[i])+j);
            share_setshare(ans[i], j, e3, i*len(x[i])+j);
            //share_free(e[i][j]);
        }
        //free(e[i]);
    }

    //free(e);
    _free(e3);
    free(d);

    return ans;
}

int CalcParamInEquality(Partition par) {
    int N = par->m + 1;
    N = 1 << (blog(N - 1) + 1);
    return N;
}

share_array EqualityConst2_channel(share_array x, share_array y, share_t new_q, int channel) {
    if (len(x) != len(y)) {
        printf("LongEqualityConst_channel:  len(x) = %d len(y)  = %d\n", len(x), len(y));
        exit(1);
    }
    if (order(x) != order(y)) {
        printf("LongEqualityConst_channel: order(x) = %d order(y) = %d\n", order(x), order(y));
        exit(1);
    }
    if (order(x) != 1 << (blog(order(x) - 1) + 1)) {
        printf("LongEqualityConst_channel: order(x) = %d\n", order(x));
        exit(1);
    }

    if (_party == -1) {
      int n = len(x);
      share_array ans = _const(n, 0, new_q);
      NEWITER(itr_x, x);
      NEWITER(itr_y, y);
      NEWITER(itr_ans, ans);
      for (int i = 0; i < n; ++i) {
        share_t z = (pa_iter_get(itr_x) == pa_iter_get(itr_y));
        pa_iter_set(itr_ans, z);
      }
      pa_iter_flush(itr_ans);
      pa_iter_free(itr_x);
      pa_iter_free(itr_y);
      return ans;
    }

    share_t old_q = order(x);
    int l = blog(old_q - 1) + 1;
    int n = len(x);

    Partition par = MakeEqualityPatition(l);
    //Partition par = MakeEqualityPatition3(l);

    share_array d;
    if (_party == 0 || _party == 1) {  // TODO: party0はどうするか？
        d = vsub(x, y);
    }
    else if (_party == 2) {
        d = vsub(y, x);
    }

    share_t *raw_d;
    NEWA(raw_d, share_t, n);
    share_t **partitioned_raw_d;
    NEWA(partitioned_raw_d, share_t*, n);
    for (int i = 0; i < n; ++i) {
        raw_d[i] = share_getraw(d, i);
        partitioned_raw_d[i] = Expand(raw_d[i], old_q, par);
    }
    _free(d);
    free(raw_d);

    share_array *p, *q;
    NEWA(p, share_array, par->m);
    NEWA(q, share_array, par->m);
    for (int i = 0; i < par->m; ++i) {
        p[i] = share_const(n, 0, 1<<par->del[i]);
        q[i] = share_const(n, 0, 1<<par->del[i]);
        for (int j = 0; j < n; ++j) {
            if (_party == 0 || _party == 1) {  // TODO: party0はどうするか？
                share_setraw(p[i], j, partitioned_raw_d[j][i]);
            }
            else if (_party == 2) {
                share_setraw(q[i], j, partitioned_raw_d[j][i]);
            }
        }
    }
    for (int i = 0; i < n; ++i) {
      free(partitioned_raw_d[i]);
    }
    free(partitioned_raw_d);

    share_t *mid_q;
    NEWA(mid_q, share_t, par->m);
    share_t N = CalcParamInEquality(par);
    //share_t N = CalcParamInOverflow3(par); // 適当
    for (int i = 0; i < par->m; ++i) {
        //mid_q[i] = par->m + 1;
        mid_q[i] = N;
    }

    share_array *f = ParallelEqualityConst1_channel(par->m, p, q, mid_q, channel);
    // for (int i = 0; i < par->m; ++i) {
    //     printf("f[%d]: ", i);
    //     share_array f_r = share_reconstruct(f[i]);
    //     share_print(f_r);
    // }
    free(mid_q);

    for (int i = 0; i < par->m; ++i) {
        _free(p[i]);
        _free(q[i]);
    }
    free(p);
    free(q);


    //share_array a = share_const(n, 0, par->m + 1);  // ここの位数はpar->m + 1であってる？
    share_array a = share_const(n, 0, N);

    for (int i = 0; i < n; ++i) {
        share_t r = 0;
        for (int j = 0; j < par->m; ++j) {
            //r = (r + share_getraw(f[j], i)) % (par->m + 1);
            r = (r + share_getraw(f[j], i)) % N;
        }
        share_setraw(a, i, r);
    }
    for (int j = 0; j < par->m; ++j) _free(f[j]);
    free(f);

    share_array *g = Unitv_channel(a, new_q, channel);
    _free(a);
    share_array ans = share_const(n, 0, new_q);
    for (int i = 0; i < n; ++i) {
        if (_party == 0) {
            if (share_getraw(x, i) == share_getraw(y, i)) {
                share_setraw(ans, i, 1);
            }
            else {
                share_setraw(ans, i, 0);
            }
            share_free(g[i]);
        }
        else {
            share_setshare(ans, i, g[i], par->m);
            share_free(g[i]);
        } 
    }

    Partition_free(par);
    free(g);

    return ans;
}
#define EqualityConst(x, y) EqualityConst2_channel(x, y, 2, 0)
#define EqualityConst_channel(x, y, channel) EqualityConst2_channel(x, y, 2, channel)


// return [x <= y]
// order of outputs is two
share_array Comparison1_channel(share_array x, share_array y, int channel) {
    int n = len(x);
    int q = order(x);
    int l = blog(q - 1) + 1;

    if (len(x) != len(y)) {
        printf("Comparison1  len(x) = %d len(y) = %d\n", len(x), len(y));
        exit(1);
    }
    if (order(x) != order(y)) {
        printf("Comparison1  order(x) = %d order(y) = %d\n", order(x), order(y));
        exit(1);
    }
    if (q != 1 << (blog(q - 1) + 1)) {
        printf("Comparison1  order(x) = %d\n", order(x));
        exit(1);
    }
    
    share_array lt = share_const(n, 0, 2);
    for (int i = 0; i < n; ++i) {
        share_t z = (share_t)(share_getraw(x, i) <= share_getraw(y, i));
        share_setraw(lt, i, z);
    }

    share_array d = vsub(x, y);
    //share_array d = vsub(y, x); // こっちが正しい？
    share_array ofd, ofx, ofy;

#if 0
    share_pair ofd_p = OverflowConst1_channel(d, 2, channel);
    share_pair ofx_p = OverflowConst1_channel(x, 2, channel);
    share_pair ofy_p = OverflowConst1_channel(y, 2, channel);

    ofd = ofd_p.y;
    ofx = ofx_p.y;
    ofy = ofy_p.y;

    share_free(ofd_p.x);
    share_free(ofx_p.x);
    share_free(ofy_p.x);
#else 
    share_array dxy[3];
    dxy[0] = share_dup(d);
    dxy[1] = share_dup(x);
    dxy[2] = share_dup(y);
    share_t qs[3] = {2, 2, 2};

    share_pair *ofs = ParallelOverflowConst1_channel(3, dxy, qs, channel);
    ofd = ofs[0].y;
    ofx = ofs[1].y;
    ofy = ofs[2].y;

    free(ofs[0].x);
    free(ofs[1].x);
    free(ofs[2].x);
    share_free(dxy[0]);
    share_free(dxy[1]);
    share_free(dxy[2]);
#endif

    share_array b = share_const(n, 1, 2);
    // vadd_(b, d);
    vadd_(b, ofd);
    vadd_(b, ofx);
    vadd_(b, ofy);

    share_free(d);
    share_free(lt);
    share_free(ofd);
    share_free(ofx);
    share_free(ofy);

    if (_party == 0) {
        for (int i = 0; i < n; ++i) {
            if (share_getraw(x, i) <= share_getraw(y, i)) {
                share_setraw(b, i, 1);
            }
            else {
                share_setraw(b, i, 0);
            }
        }
    }

    return b;
}

//////////////////////////////////////////////////////////
// x <= y のとき 1 を返す
// x, y の位数は 8 以上の 2 のべき乗
// 値は位数の半分未満
//////////////////////////////////////////////////////////
share_array Comparison2_channel(share_array x, share_array y, int channel) 
{
    int n = len(x);
    int q = order(x);
    int l = blog(q - 1) + 1;

    if (len(x) != len(y)) {
        printf("Comparison2  len(x) = %d len(y) = %d\n", len(x), len(y));
        exit(1);
    }
    if (order(x) != order(y)) {
        printf("Comparison2  order(x) = %d order(y) = %d\n", order(x), order(y));
        exit(1);
    }
    //if (q != 1 << (blog(q - 1) + 1)) {
    if (q != 1 << (blog(q - 1) + 1) || q < 8) {
        printf("Comparison2  order(x) = %d\n", order(x));
        exit(1);
    }
    if (_party == -1) {
      int n =len(x);
      _ b = share_const(n, 0, 2);
      NEWITER(itr_b, b);
      NEWITER(itr_x, x);
      NEWITER(itr_y, y);
      for (int i = 0; i < n; ++i) {
        pa_iter_set(itr_b, pa_iter_get(itr_x) <= pa_iter_get(itr_y));
      }
      pa_iter_flush(itr_b);
      pa_iter_free(itr_x);
      pa_iter_free(itr_y);
      return b;
    }
    
    share_array lt = share_const(n, 0, 2);
    for (int i = 0; i < n; ++i) {
        share_t z = (share_t)(share_getraw(x, i) <= share_getraw(y, i));
        share_setraw(lt, i, z);
    }

    //share_array d = vsub(x, y);
    share_array d = vsub(y, x);

#if 0
    share_array ofd, ofx, ofy;
    ofd = OverflowConst2_channel(d, channel);
    ofx = OverflowConst2_channel(x, channel);
    ofy = OverflowConst2_channel(y, channel);

//    printf("d "); _print(d); _print_debug(d);
//    printf("x "); _print(x); _print_debug(x);
//    printf("y "); _print(y); _print_debug(y);
//    printf("ofd "); _print_debug(ofd);
//    printf("ofx "); _print_debug(ofx);
//    printf("ofy "); _print_debug(ofy);
//    printf("lt "); _print(lt);

    share_array b = share_const(n, 1, 2);
    // vadd_(b, d);
    vadd_(b, ofd);
    vadd_(b, ofx);
    vadd_(b, ofy);
    vadd_(b, lt);
    //printf("b "); _print_debug(b);
    share_free(ofd);
    share_free(ofx);
    share_free(ofy);
#else
    // ここにoverflow2の並列処理を実装した関数を書く
    _ tmp = _const(n*3, 0, order(d));
    pa_iter itr_tmp = pa_iter_new(tmp->A); 
    pa_iter itr_d = pa_iter_new(d->A); 
    for (int i=0; i<n; i++) pa_iter_set(itr_tmp, pa_iter_get(itr_d));
    pa_iter_free(itr_d);
    pa_iter itr_x = pa_iter_new(x->A); 
    for (int i=0; i<n; i++) pa_iter_set(itr_tmp, pa_iter_get(itr_x));
    pa_iter_free(itr_x);
    pa_iter itr_y = pa_iter_new(y->A); 
    for (int i=0; i<n; i++) pa_iter_set(itr_tmp, pa_iter_get(itr_y));
    pa_iter_free(itr_y);
    pa_iter_flush(itr_tmp);
    //printf("tmp "); _print_debug(tmp);
    _ of = OverflowConst2_channel(tmp, channel);
    //printf("of "); _print_debug(of);
    _ b = share_const(n, 0, 2);
    itr_d = pa_iter_pos_new(of->A, 0);
    itr_x = pa_iter_pos_new(of->A, n);
    itr_y = pa_iter_pos_new(of->A, 2*n);
    pa_iter itr_lt = pa_iter_new(lt->A);
    pa_iter itr_b = pa_iter_new(b->A);
    for (int i=0; i<n; i++) {
      share_t z = 0;
      if (_party <= 1) z = 1;
      z ^= pa_iter_get(itr_d) ^ pa_iter_get(itr_x) ^ pa_iter_get(itr_y) ^ pa_iter_get(itr_lt); 
      pa_iter_set(itr_b, z);
    }
    pa_iter_flush(itr_b);
    pa_iter_free(itr_d);
    pa_iter_free(itr_x);
    pa_iter_free(itr_y);
    pa_iter_free(itr_lt);
    _free(tmp);
    _free(of);
    //printf("b  "); _print_debug(b);
    //printf("b2 "); _print_debug(b2);
#endif


    share_free(d);
    share_free(lt);

    if (_party == 0) {
        for (int i = 0; i < n; ++i) {
            if (share_getraw(x, i) <= share_getraw(y, i)) {
                share_setraw(b, i, 1);
            }
            else {
                share_setraw(b, i, 0);
            }
        }
    }

    return b;
}


#if 0
share_array* Unitv_channel(share_array x, int new_q, int channel) {
    int n = len(x);
    share_t old_q = order(x);

    share_array r, v, s, m_;
    share_array *ans;
    NEWA(ans, share_array, n);



#ifdef NO_PRECOMPUTE
    share_pair p = Unitv_prep_channel(n, old_q, new_q, channel);
    // printf("x: ");  share_print(share_reconstruct(x));
    r = p.x;    //printf("r: ");share_print(share_reconstruct(r));
    v = p.y;    //printf("v: ");share_print(share_reconstruct(v));
#else
    // ここには事前計算したファイルからの読み取りのプログラムを書く
#endif
    s = vsub(r, x);
    m_ = share_reconstruct_channel(s, channel); // 通信1回
    for (int i = 0; i < n; ++i) {
        share_t m = pa_get(m_->A, i);//printf("m: %d\n", m);
        ans[i] = share_const(old_q, 0, new_q);
        for (int j = 0; j < old_q; ++j) {
            u64 a = pa_get(v->A, old_q*i + (j+m) % old_q);
            pa_set(ans[i]->A, j, a);
        }
    }

    share_free(r);
    share_free(v);
    share_free(m_);
    share_free(s);
    
    return ans;
}
#define Unitv(x, new_q) Unitv_channel(x, new_q, 0)
#endif

// typedef struct {
//     share_t q;  // the modulus of share.

// // P0
    
// } *dshare_shift;


// // Preprocessing for Unitv
// // Note that N and N_ of pre_unit and Unitv should be same values respectively.
// pre_unit Unitv_prep(share_t N, share_t N_) {
//     int a = RANDOM0(N);

// }

share_array MSNZB(share_array);

// share_array* MSNZBs_channel(int n, share_array *g, int channel) {
//     share_array *ans;
//     NEWA(ans, share_array, n);
//     int t = len(g[0]);

//     share_array *v = Unitvb_channel(n, g, 2, channel);
//     for (int i = 0; i < n; ++i) {
//         ans[i] = share_const(t, 0, 2);
//         for (int j = 0; j < t; ++j) {
//             share_t x = 0;
//             for (int k = (1<<j); k < (1<<(j+1)); ++k) {
//                 x = (x + share_getraw(v[i], k)) % 2;
//             }
//             share_setraw(ans[i], j, x);
//         }
//         share_free(v[i]);
//     }

//     free(v);

//     return ans;
// }



_ MSNZB1_channel(_bits b, share_t new_q, int channel)
{
  int n = len_bits(b);
  int t = depth_bits(b);
  int m = 1 << t;

  share_array v = UnitvB_channel(b, new_q, channel);

  _ c = share_const(n*t, 0, new_q);
  for (int p = 0; p < n; ++p) {
    for (int i = 0; i < t; ++i) {
      share_t x = 0;
      for (int j = (1<<i); j < (1<<(i+1)); ++j) {
        x = (x + share_getraw(v, p * m + j)) % new_q;
      }
      share_setraw(c, p * t + i, x);
      }
   }
   _free(v);

   return c;
}

_ MSNZB_channel(_bits b, share_t new_q, int channel)
{

  int n = len_bits(b);
  int l = depth_bits(b);

  Partition par = MakeOverflowPatition2(l);

  int m = 1 << l;

  share_array v = UnitvB_channel(b, new_q, channel);

  _ c = share_const(n*m, 0, new_q);
  for (int p = 0; p < n; ++p) {
    for (int i = 0; i < l; ++i) {
      share_t x = 0;
      for (int j = (1<<i); j < (1<<(i+1)); ++j) {
        x = (x + share_getraw(v, p * m + j)) % new_q;
      }
      share_setraw(c, p * l + i, x);
      }
   }
   _free(v);

   return c;
}

#endif 