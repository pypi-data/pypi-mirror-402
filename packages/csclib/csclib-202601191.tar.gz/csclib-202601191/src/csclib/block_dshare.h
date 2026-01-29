// もとのdshareの中でbという識別子を使っているため，ブロックサイズをbsで表している．
#if 0


#ifndef _BLOCK_DSHARE_H
#define _BLOCK_DSHARE_H

#include <stdio.h>
#include <stdlib.h>

#include "share.h"
//#include "block_share.h"
#include "dshare.h"

// typedef struct {
//     // public
//     int n;  // the number of the blocks in the array
//     int bs;  // the size of block
//     share_t q;  // the order of elements of the array

//     // P0
//     perm pi;        // the length of pi, p1, etc. are n
//     perm p1, p2p;   // pi = p1 * p1p
//     perm p2, p1p;   // pi = p2 * p2p

//     // P1, P2
//     perm g, gp; // the length of g and gp are n

//     // correlated_random
//     // P0
//     perm a1, b1;    // the length of a1, b1, etc. are n*b
//     perm a2, b2;    // b1 = a2 * p1p + c, b2 = a1 * p2p - c
//     // P1, P2
//     perm a, b;
// }* block_dshare;

// p is of length n*b 
// q is of length n
#if 0
static perm block_perm_apply(int bs, perm p, perm q) {
    perm pq;
    int k = p->w;
    int n = q->n;
    pq = pa_new(n*bs, k);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
            pa_set(pq, i*bs + j, pa_get(p, pa_get(q, i)*bs + j));
        }
    }
    return pq;
}
#endif

// static block_share_array block_share_perm(b_ x, perm pi) {
//     if (x->n != pi->n) {
//         printf("block_share_perm: x->n %d pi->n %d\n", x->n, pi->n);
//     }
//     b_ ans = _bdup(x);
//     int n = block_len(x);
//     int bs = block_size(x);
//     for (int i = 0; i < n; ++i) {
//         for (int j = 0; j < bs; ++j) {
//             _setshare(ans->a, i*bs + j, x->a, pa_get(pi, i) * bs + j);
//         }
//     }
//     return ans;
// }

// bs: block size
#if 0
static share_array block_share_perm(int bs, _ x, perm pi) {
    if (x->n/bs != pi->n) {
        printf("block_share_perm: x->n %d pi->n %d\n", x->n, pi->n);
    }
    _ ans = _dup(x);
    int n = len(x)/bs;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < bs; ++j) {
            _setshare(ans, i*bs + j, x, pa_get(pi, i) * bs + j);
        }
    }
    return ans;
}
#endif

#if 0
static void block_dshare_correlated_random_channel(int bs, dshare ds, int channel) {
    int n = ds->n;
    share_t q = ds->q;
    int k = blog(q - 1) + 1;
    if (_party <= 0) {
        ds->a1 = pa_new(n*bs, k);
        ds->a2 = pa_new(n*bs, k);
        perm c = pa_new(n*bs, k);

        for (int i = 0; i < n*bs; ++i) {
            pa_set(ds->a1, i, RANDOM(mt1[channel], q));
        }
        for (int i = 0; i < n*bs; ++i) {
            pa_set(ds->a2, i, RANDOM(mt2[channel], q));
        }
        for (int i = 0; i < n*bs; ++i) {
            pa_set(c, i, RANDOM(mt0, q));
        }
        ds->b1 = block_perm_apply(bs, ds->a2, ds->p1p);
        ds->b2 = block_perm_apply(bs, ds->a1, ds->p2p);

        for (int i = 0; i < n*bs; ++i) {
            pa_set(ds->b1, i, MOD(pa_get(ds->b1, i) + pa_get(c, i)));
            pa_set(ds->b2, i, MOD(pa_get(ds->b2, i) + q - pa_get(c, i)));
        }

        perm_free(c);

        if (_party == 0) {
            mpc_send(channel*2+TO_PARTY1, ds->b1->B, pa_size(ds->b1));    send_3 += pa_size(ds->b1);
            mpc_send(channel*2+TO_PARTY2, ds->b2->B, pa_size(ds->b2));
        }
    }
    else {  // party 1, 2
        ds->a = pa_new(n*bs, k);
        ds->b = pa_new(n*bs, k);
        
        for (int i = 0; i < n*bs; ++i) {
            pa_set(ds->a, i, RANDOM(mts[channel], q));
        }
        mpc_recv(channel*2+FROM_SERVER, (char *)ds->b->B, pa_size(ds->b));
    }
}
#define block_dshare_correted_random(ds) block_dshare_correlated_random_channel(ds, 0);
#endif

#if 0
static dshare block_dshare_new_channel(int n, int bs, perm pi, share_t q, int channel) {
    NEWT(dshare, ds);
    ds->n = n;
    ds->q = q;
    if (_party <= 0) {
        ds->pi = perm_id(n);
        for (int i = 0; i < n; ++i) {
            pa_set(ds->pi, i, pa_get(pi, i));
        }

        perm p1_inv, p2_inv;
        ds->p1 = perm_random(mt1[channel], n);
        p1_inv = perm_inverse(n, ds->p1);
        ds->p2p = perm_apply(n, p1_inv, pi);

        ds->p2 = perm_random(mt2[channel], n);
        p2_inv = perm_inverse(n, ds->p2);
        ds->p1p = perm_apply(n, p2_inv, pi);
        perm_free(p1_inv);
        perm_free(p2_inv);

        if (_party == 0) {
            mpc_send(channel*2+TO_PARTY1, ds->p1p->B, pa_size(ds->p1p));  //send_4 += pa_size(ds->p1p);
            mpc_send(channel*2+TO_PARTY2, ds->p2p->B, pa_size(ds->p2p));
        }
    }
    else {
        ds->g = perm_random(mts[channel], n);
        ds->gp = perm_id(n);
        mpc_recv(channel*2+FROM_SERVER, (char *)ds->gp->B, pa_size(ds->gp));
    }

    block_dshare_correlated_random_channel(bs, ds, channel);

    return ds;
}
#define block_dshare_new(n, bs, pi, q) block_dshare_new_channel(n, bs, pi, q, 0)
#endif

// static block_dshare block_dshare_new_party0(int n, int bs, share_t q);
// static block_dshare block_dshare_new2_channel(int n, int bs, perm pi, share_t q, int channel);


// static void block_dshare_free(block_dshare ds) {
//     if (_party <= 0) {
//         perm_free(ds->pi);
//         perm_free(ds->p1);
//         perm_free(ds->p1p);
//         perm_free(ds->p2);
//         perm_free(ds->p2p);
//         perm_free(ds->a1);
//         perm_free(ds->b1);
//         perm_free(ds->a2);
//         perm_free(ds->b2);
//     }
//     else {
//         perm_free(ds->g);
//         perm_free(ds->gp);
//         perm_free(ds->a);
//         perm_free(ds->b);
//     }
//     free(ds);
// }

// static void block_dshare_free2(block_dshare ds) {
//     if (_party <= 0) {
//         perm_free(ds->pi);
//         perm_free(ds->p1);
//         perm_free(ds->p1p);
//         perm_free(ds->p2);
//         perm_free(ds->p2p);
// //      perm_free(ds->a1);
// //      perm_free(ds->b1);
// //      perm_free(ds->a2);
// //      perm_free(ds->b2);
//     }
//     else {
//         perm_free(ds->g);
//         perm_free(ds->gp);
// //      perm_free(ds->a);
// //      perm_free(ds->b);
//     }
//     free(ds);
// }

// static void block_dshare_free3(block_dshare ds) {
//     if (_party <= 0) {
//         perm_free(ds->a1);
//         perm_free(ds->b1);
//         perm_free(ds->a2);
//         perm_free(ds->b2);
//     }
//      else {
//         perm_free(ds->a);
//         perm_free(ds->b);
//     }
// }

#if 0
static share_array block_dshare_shuffle_channel(int bs, share_array x, dshare ds, int channel) {
    int n = len(x) / bs;
    share_t q = order(x);
    share_array v;
    if (n != ds->n) {
        printf("block_dshare_shuffle_channel: n %d ds->n %d\n", n, ds->n);
        exit(EXIT_FAILURE);
    }

    if (_party <= 0) {
        v = block_share_perm(bs, x, ds->p1);
        // printf("v ok\n");   fflush(stdout);
        for (int i = 0; i < n * bs; ++i) {
            pa_set(v->A, i, MOD(10*q + pa_get(v->A, i) + pa_get(ds->a1, i)));
        }
    }
    else {
        v = block_share_perm(bs, x, ds->g);
        for (int i = 0; i < n * bs; ++i) {
            pa_set(v->A, i, MOD(10*q + pa_get(v->A, i) + pa_get(ds->a, i)));
        }
    }

    share_array y;
    if (_party <= 0) {
        y = block_share_perm(bs, v, ds->p2p);
        for (int i = 0; i < n * bs; ++i) {
            pa_set(y->A, i, MOD(10*q + pa_get(y->A, i) - pa_get(ds->b2, i)));
        }
        perm tmp = block_perm_apply(bs, ds->a2, ds->p1p);
        for (int i = 0; i < n * bs; ++i) {
            pa_set(y->A, i, MOD(10*q + pa_get(y->A, i) + pa_get(tmp, i) - pa_get(ds->b1, i)));
        }
        perm_free(tmp);
        // send_8 += pa_size(v->a->A);
    }
    else {
        share_array z = share_dup(v);
        mpc_exchange_channel(v->A->B, z->A->B, pa_size(v->A), channel);
        y = block_share_perm(bs, z, ds->gp);
        for (int i = 0; i < n * bs; ++i) {
            pa_set(y->A, i, MOD(10 * q + pa_get(y->A, i) - pa_get(ds->b, i)));
        }
        _free(z);
    }
    _free(v);

    return y;
}
#define block_dshare_shuffle(bs, x, ds) block_dshare_shuffle_channel(bs, x, ds, 0)
#endif

// block_dshareの計算（前計算）
// n: 順列の長さ
// b: 順列が適用されるlock_share_arrayのブロックサイズ
// m: 順列の個数
// void block_dshare_precomp(int m, int n, int b, share_t q, int inverse, char *fname) {
//     FILE *f1, *f2;

//     int kn = blog(n-1) + 1;

//     // 各パーティが前計算の結果を保存するファイル名を作成
//     char *fname1 = precomp_fname(fname, 1); // パーティ１が保存するファイルの名前
//     char *fname2 = precomp_fname(fname, 2); // パーティ２が保存するファイルの名前

//     f1 = fopen(fname1, "wb");
//     f2 = fopen(fname2, "wb");

//     unsigned long init[5] = {0x123, 0x234, 0x345, 0x456, 0};
//     MT m0 = MT_init_by_array(init, 5);

//     unsigned long init1[5] = {0x123, 0x234, 0x345, 0x456, 1};
//     init1[4] = 1;
//     mt1[0] = MT_init_by_array(init1, 5);

//     unsigned long init2[5] = {0x123, 0x234, 0x345, 0x456, 0};
//     init2[4] = 2;
//     mt2[0] = MT_init_by_array(init2, 5);

//     perm g = perm_random(m0, n);
//     block_dshare ds1, ds2;
//     share_t qq = max(1<<kn, q);

//     if (inverse == 0) {
//         perm g_inv = perm_inverse(n, g);
//         ds1 = block_dshare_new(n, b, g, 1<<kn);
//         ds2 = block_dshare_new(n, b, g_inv, q);
//         perm_free(g_inv);
//     }
//     else {
//         ds1 = block_dshare_new(n, b, g, qq);
//         ds2 = block_dshare_new(n, b, g, qq);
//     }
//     perm_free(g);

//     // いろいろ書き換えた方がいいが，中身がまだわかってないので一旦放置
//     // precomp_write_seed(f1, n*2, qq, init1); // p1 と a1 を作るために 2n 個の乱数を使う
//     // precomp_write_seed(f2, n*2, qq, init2); // p2 と a2
//     // precomp_write_share(f1, ds1->p1p);
//     // precomp_write_share(f2, ds1->p2p);
//     // precomp_write_share(f1, ds1->b1);
//     // precomp_write_share(f2, ds1->b2);
//     // precomp_write_share(f1, ds2->p1p);
//     // precomp_write_share(f2, ds2->p2p);
//     // precomp_write_share(f1, ds2->b1);
//     // precomp_write_share(f2, ds2->b2);

//     // MT_free(m0);
//     // dshare_free(ds1);
//     // dshare_free(ds2);

//     // fclose(f1);
//     // fclose(f2);
// }

// 一旦宣言だけしておく
// static void block_dshare_new_precomp(DS_tables tbl, int n, int b, share_t q_x, share_t q_sigma, block_dshare *ds1_, block_dshare *ds2_);

#if 0
static share_array block_AppPerm_fwd_channel(int bs, share_array x, share_array sigma, int channel) {
    int n = len(x) / bs;
    if (n != len(sigma)) {
        printf("block_AppPerm_fwd_channel: block_len(x) %d len(sigma) %d\n", n, len(sigma));
    }
    dshare ds1;
    dshare ds2;

    int ln = blog(n-1) + 1;
    // ifの条件が成立している時の処理は書き換える必要があるかも．
    if (0 && (n == 1<<ln)&&(ln <= 10)) {
        char fname[100];
        //printf("ln = %d\n", ln);
        sprintf(fname, "PRE_DS_n%d_w%d.dat", ln, 30);
        DS_tables DS_tbl = DS_tables_read(fname);
        dshare_new_precomp(DS_tbl, n, order(x), order(sigma), &ds1, &ds2);
        DS_tables_free(DS_tbl);
    } else {
        //  printf("n = %d\n", n);
        perm g;
        if (_party == 0) {
            g = perm_random(mt0, n);
        } else {
            g = perm_id(n);
        }
        perm g_inv = perm_inverse(n, g);

        ds1 = dshare_new_channel(n, g, order(sigma), channel);
        ds2 = block_dshare_new_channel(n, bs, g_inv, order(x), channel);
        perm_free(g_inv);
        perm_free(g);
    }
    // ここまでが前計算

    _ w;
    _ rho = dshare_shuffle_channel(sigma, ds1, channel);
    if (_party <= 0) {
        w = block_share_perm(bs, x, share_raw(rho));
        // send_5 += pa_size(w->A);
    }
    else {
        _ r = share_reconstruct_channel(rho, channel);
        w = block_share_perm(bs, x, share_raw(r));
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
#endif

#if 0
static share_array block_AppPerm_channel(int bs, _ x, _ sigma, int channel) {
    _ ans = block_AppPerm_fwd_channel(bs, x, sigma, channel);
    return ans;
}
#define block_AppPerm(bs, x, sigma) block_AppPerm_channel(bs, x, sigma, 0)

static void block_AppPerm_channel_(int bs, _ x, _ sigma, int channel) {
    _ ans = block_AppPerm_fwd_channel(bs, x, sigma, channel);
    _move_(x, ans);
}
#define block_AppPerm_(bs, x, sigma) block_AppPerm_channel_(bs, x, sigma, 0)
#endif

#if 0
static share_array block_AppPerm_inverse_channel(int bs, share_array x, _ sigma, int channel) {
    int n = len(x) / bs;
    if (n != len(sigma)) {
        printf("block_AppPerm_inverse: block_len(x) %d len(sigma) %d\n", n, len(sigma));
    }

    dshare ds1;
    dshare ds2;

    int ln = blog(n-1) + 1;
    // ifの条件が成立している時の処理は書き換える必要がある．
    if (0 && (n == 1<<ln)&&(ln <= 10)) {
        // char fname[100];
        // //printf("ln = %d\n", ln);
        // sprintf(fname, "PRE_DS_n%d_w%d.dat", ln, 30);
        // DS_tables DS_tbl = DS_tables_read(fname);
        // dshare_new_precomp(DS_tbl, n, block_order(x), order(sigma), &ds1, &ds2);
        // DS_tables_free(DS_tbl);
    } else {
        //  printf("n = %d\n", n);
        perm g;
        if (_party == 0) {
            g = perm_random(mt0, n);
        } else {
            g = perm_id(n);
        }

        ds1 = dshare_new_channel(n, g, order(sigma), channel);
        ds2 = block_dshare_new_channel(n, bs, g, order(x), channel);
        
        perm_free(g);
    }
    // ここまでが前計算

    _ rho = dshare_shuffle_channel(sigma, ds1, channel);
    // printf("rho ");  share_print(rho);  fflush(stdout);
    share_array z = block_dshare_shuffle_channel(bs, x, ds2, channel);
    // printf("z   ");     share_print(z);  fflush(stdout);
    _ r = share_reconstruct_channel(rho, channel);  // send_6 += pa_size(r->A);
    // printf("r   ");  share_print(r);    fflush(stdout);
    perm rho_inv = perm_inverse(n, share_raw(r));
    share_array ans = block_share_perm(bs, z, rho_inv);
    // printf("ans "); share_print(ans);  fflush(stdout);
    _free(r);
    _free(z);
    perm_free(rho_inv);
    _free(rho);
    dshare_free(ds1);
    dshare_free(ds2);

    return ans;
}
#endif

#if 0
static void block_AppInvPerm_channel_(int bs, share_array x, _ sigma, int channel) {
    share_array ans = block_AppPerm_inverse_channel(bs, x, sigma, channel);
    _move_(x, ans);
}
#define block_AppInvPerm_(bs, x, sigma) block_AppInvPerm_channel_(bs, x, sigma, 0)
#endif

// ランダムな置換gを生成し，それをxに作用させ，gのinverseを返す．
// generate a random permutation g, apply it to x and return the inverse of g.
// static _ block_AppRandomPerm_inverse_channel(block_share_array x, int channel) {
//     int n = block_len(x);
//     int b = block_size(x);
//     block_dshare ds1, ds2;  // ds1 is not used.

//     _ g;
//     // permutationの位数がnになっているが，n以上の2の冪乗に変えた方が良かったりしないか？
//     if (_party == 0) {
//         g = _random_perm(n);
//     }
//     else {
//         g = Perm_ID(n, n);
//     }

//     ds2 = block_dshare_new_channel(n, b, share_raw(g), block_order(x), channel);

//     block_share_array ans;
//     ans = block_dshare_shuffle_channel(x, ds2, channel);
//     _bmove_(x, ans);

//     block_dshare_free(ds2);

//     packed_array ginv = perm_inverse(n, g->A);
//     free(g->A);
//     g->A = ginv;

//     return g;
// }

// // generate a random permutation g, apply it to x and sigma and return g.
// // why does this function's name include "inverse"?
// static _ block_AppRandomPerm2_inverse_channel(block_share_array x, _ sigma, int channel) {
//     int n = block_len(x);
//     int b = block_size(x);
//     block_dshare ds1, ds2;

//     _ g;
//     // gの位数はn以上の最小の２の冪乗としたほうが綺麗？
//     if (_party == 0) {
//         g = _random_perm(n);
//     }
//     else {
//         g = Perm_ID2(n, n);
//     }

//     share_t ord = max(block_order(x), order(sigma));

//     ds2 = block_dshare_new_channel(n, b, share_raw(g), ord, channel);
    
//     _ ans;
//     ans = block_dshare_shuffle_channel(x, ds2, channel);
//     _bmove_(x, ans);

//     // can reuse same ds2 twice?
//     ans = block_dshare_shuffle_channel(sigma, ds2, channel);
//     _bmove_(sigma, ans);

//     block_dshare_free(ds2);
//     return g;
// }

// // 
// static block_share_array block_AppPerm_new_channel(block_share_array x, _ sigma, int inverse, int channel) {
//     block_dshare ds;
//     int n = block_len(x);
//     int b = block_size(x);

//     if (n != len(sigma)) {
//         printf("block_AppPerm: block_len(x) %d len(sigma) %d\n", n, len(sigma));
//     }
//     perm g;
//     if (_party == 0) {
//         g = perm_random(mt0, n);
//     }
//     else {
//         g = perm_id(n);
//     }

//     block_share_array z, w;
//     ds = block_dshare_new_channel(n, b, g, order(x), channel);
//     _ rho
// }

#endif

#endif
