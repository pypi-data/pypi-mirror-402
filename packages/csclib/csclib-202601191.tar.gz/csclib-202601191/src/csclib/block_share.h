#ifndef _BLOCK_SHARE_H
#define _BLOCK_SHARE_H

#include <stdio.h>
#include <stdlib.h>

#include "share.h"
#include "../RankORAM/rank_oram.h"

#if 0

typedef struct {
    int n;  // ブロック数
    int b;  // １ブロック中の要素数
    share_t q;  // mod
    share_array a;  // nb個の要素からなるシェア配列
    int own;    // 1の時は解放しない
}* block_share_array;
typedef block_share_array b_;

void block_share_print(block_share_array x, char *x_string) {
    printf("printing party %d's \"%s\"\n", _party, x_string);
    printf("length: %d block_size: %d order: %d\n", x->n, x->b, x->q);
    for (int i = 0; i < x->n; ++i) {
        printf("(");
        for (int j = 0; j < x->b; ++j) {
            printf("%2d ", (int)pa_get(x->a->A, i * x->b + j));
        }
        printf(")  ");
    }
    printf("\n");
}

static int block_len(block_share_array x) {
    return x->n;
}

static int block_size(block_share_array x) {
    return x->b;
}

static share_t block_order(block_share_array x) {
    return x->q;
} 

static packed_array block_share_raw(block_share_array x) {
    return x->a->A;
}

static void mpc_send_block_share(int party_to, b_ x) {
    mpc_send_share(party_to, x->a);
}

static void mpc_recv_block_share(int party_from, b_ x) {
    mpc_recv_share(party_from, x->a);
}

static void mpc_exchange_block_share(b_ b_share_send, b_ b_share_recv) {
    mpc_exchange_share(b_share_send->a, b_share_recv->a);
}

// static void block_share_print(b_ x) {
//     printf("n = %d b = %d q = %d w = %d party %d: ", x->n, x->b, x->q, x->a->A->w, _party);
//     for (int i = 0; i < x->n; ++i) {
//         printf("(");
//         for (int j = i * x->b; j < (i + 1) * x->b; ++j) {
//             printf("%d", (int)pa_get(x->a->A, i));
//             if (j % x->b != x->b - 1) {
//                 printf(" ");
//             }
//         }
//         printf(") ");
//     }
// }
#define _bprint block_share_print

static void block_share_fprint(FILE *f, block_share_array x) {
    fprintf(f, "n = %d b = %d q = %d w = %d party %d: ", x->n, x->b, x->q, x->a->A->w, _party);
    for (int i = 0; i < x->n; ++i) {
        fprintf(f, "(");
        for (int j = i * x->b; j < (i + 1) * x->b; ++j) {
            fprintf(f, "%d", (int)pa_get(x->a->A, i));
            if (j % x->b != x->b - 1) {
                fprintf(f, " ");
            }
        }
        fprintf(f, ") ");
    }
}
#define _bfprint block_share_fprint


static block_share_array block_share_new_channel(int n, int b, share_t q, share_t *A, int channel) {
    int i;
    NEWT(block_share_array, ans);
    int k;

    ans->n = n;
    ans->b = b;
    ans->q = q;
    ans->own = 0;
    ans->a = share_new_channel(n * b, q, A, channel);
    return ans;
}
#define block_share_new(n, b, q, A) block_share_new_channel(n, b, q, A, 0)

static void block_share_resend_channel(b_ x, int channel) {
    share_resend_channel(x->a, channel);
}
#define block_resend(x) block_share_resend_channel(x, 0);

static void block_share_free(block_share_array x) {
    share_free(x->a);
    free(x);
}
#define _bfree block_share_free

// the definition will be written later
static void block_share_save(block_share_array a, char *filename);
static block_share_array block_share_load(char *filename);

// it might be a good idea to overwrite this
static void block_share_check(block_share_array x) {
    share_check(x->a);
}

static block_share_array block_share_reconstruct_channel(block_share_array x, int channel) {
    NEWT(block_share_array, ans);
    *ans = *x;
    share_free(ans->a);
    ans->a = share_reconstruct_channel(x->a, channel);

    return ans;
}

// the definition will be overwritten later
static block_share_array block_share_reconstruct_channel_tmp(block_share_array x, int channel);

#define _breconstruct_channel block_share_reconstruct_channel
#define block_share_reconstruct(x) block_share_reconstruct_channel(x, 0)

// xの各要素にr, -rを加える
// 同じブロック中の要素にも異なるr, -rを加えている．
static void block_share_randomize(block_share_array x) {
    share_randomize(x->a);
}
#define _brandomize block_share_randomize

static block_share_array block_share_dup(block_share_array x) {
    NEWT(block_share_array, D);
    *D = *x;
    D->a = (share_array)malloc(sizeof(D->a[0]));
    D->a->n = x->a->n;
    D->a->q = x->a->q;
    D->a->A = pa_new(x->a->A->n, x->a->A->w);
    memcpy(D->a->A->B, x->a->A->B, pa_size(x->a->A));
    return D;
}
#define _bdup block_share_dup

static void block_share_move_(block_share_array x, block_share_array y) {
    share_free(x->a);
    *x = *y;
    x->a = share_dup(y->a);
    block_share_free(y);
}
#define _bmove_ block_share_move_

static block_share_array block_share_move(block_share_array x) {
    return x;
}
#define _bmove block_share_move


static void block_share_setsecret_channel(block_share_array x, int i, int j, share_t y, int channel) {
    if (i < 0 || i >= block_len(x)) {
        printf("block_share_setsecuret_channel: n %d i %d\n", block_len(x), i);
        exit(EXIT_FAILURE);
    }
    if (j < 0 || j >= block_size(x)) {
        printf("block_share_setsecuret_channel: b %d j %d\n", block_size(x), j);
        exit(EXIT_FAILURE);
    }
    
    share_setsecret_channel(x->a, i * block_size(x) + j, y, channel);
}

static void block_share_setsecretblock_channel(block_share_array x, int i, share_t *y, int channel) {
    if (i < 0 || i >= block_len(x)) {
        printf("block_share_setsecuret_channel: n %d i %d\n", block_len(x), i);
        exit(EXIT_FAILURE);
    }

    share_t *y1, *y2, q = block_order(x);
    int b = block_size(x);
    NEWA(y1, share_t, b);
    NEWA(y2, share_t, b);
    if (_party <= 0) {
        share_t r;
        for (int j = 0; j < b; ++j) {
            r = RANDOM0(q);
            y1[j] = r;
            y2[j] = (y[j] + q - r) % q;
            pa_set(x->a->A, i*b + j, y[j]);
        }
        mpc_send_queue(channel*_num_parties + TO_PARTY1, &y1, sizeof(y1[0])*b);
        mpc_send_queue(channel*_num_parties + TO_PARTY2, &y2, sizeof(y2[0])*b);
    }
    else {
        mpc_recv(channel*_num_parteis + FROM_SERVER, &y1, sizeof(y1[0])*b);
        for (int j = 0; j < b; ++j) {
            pa_set(x->a->A, i*b + j, y1[j]);
        }
    }
}

// static void share_setsecretblock_channel(int b, share_array x, int i, share_t *y, int channel) {
//     if (i < 0 || i >= block_len(x)) {
//         printf("block_share_setsecuret_channel: n %d i %d\n", block_len(x), i);
//         exit(EXIT_FAILURE);
//     }

//     share_t *y1, *y2, q = order(x);
//     //int b = block_size(x);
//     NEWA(y1, share_t, b);
//     NEWA(y2, share_t, b);
//     if (_party <= 0) {
//         share_t r;
//         for (int j = 0; j < b; ++j) {
//             r = RANDOM0(q);
//             y1[j] = r;
//             y2[j] = (y[j] + q - r) % q;
//             pa_set(x->a->A, i*b + j, y[j]);
//         }
//         mpc_send_queue(channel*2 + TO_PARTY1, &y1, sizeof(y1[0])*b);
//         mpc_send_queue(channel*2 + TO_PARTY2, &y2, sizeof(y2[0])*b);
//     }
//     else {
//         mpc_recv(channel*2 + FROM_SERVER, &y1, sizeof(y1[0])*b);
//         for (int j = 0; j < b; ++j) {
//             pa_set(x->a->A, i*b + j, y1[j]);
//         }
//     }
// }


static void block_share_setpublicblock(block_share_array x, int i, share_t *y) {
    if (i < 0 || i >= block_len(x)) {
        printf("block_share_setpublicblock: n %d i %d\n", block_len(x), i);
        exit(EXIT_FAILURE);
    }
    share_t q = x->q;
    int b = block_size(x);
    for (int j = 0; j < b; ++j) {
        if (_party == 2) {
            pa_set(x->a->A, i * b + j, 0);
        }
        else {
            pa_set(x->a->A, i * b + j, MOD(y[j]));
        }
    }
}
#define _bsetpublicb block_share_setpublicblock

// static void share_setpublicblock(int b, share_array x, int i, share_t *y) {
//     if (i < 0 || i >= len(x)) {
//         printf("share_setpublicblock: n %d i %d\n", len(x), i);
//         exit(EXIT_FAILURE);
//     }
//     share_t q = x->q;
//     //int b = block_size(x);
//     for (int j = 0; j < b; ++j) {
//         if (_party == 2) {
//             pa_set(x->a->A, i * b + j, 0);
//         }
//         else {
//             pa_set(x->a->A, i * b + j, MOD(y[j]));
//         }
//     }
// }

//set j-th element in i-th block to buplic value y
static void block_share_setpublic(block_share_array x, int i, int j, share_t y) {
    if (i < 0 || i >= x->n) {
        printf("block_share_setpublic n %d i %d\n", x->n, i);
    }
    if (j < 0 || j >= x->b) {
        printf("block_share_setpublic b %d j %d\n", x->b, j);
    }
    share_setpublic(x->a, i * x->b + j, y);
}
#define _bsetpublic block_share_setpublic

// set i-th block of x to j-th block of y
static void block_share_setshareblock(block_share_array x, int i, block_share_array y, int j) {
    if (i < 0 || i >= x->n) {
        printf("block_share_setshareblock x: n %d i %d\n", x->n, i);
    }
    if (j < 0 || j >= y->n) {
        printf("block_share_setshareblock y: n %d j %d\n", y->n, j);
    }
    if (x->q != y->q) {
        printf("block_share_setshareblock x->q %d y->q %d\n", (int)x->q, (int)y->q);
    }
    if (x->b != y->b) {
        printf("block_share_setshareblock x->b %d y->b %d\n", (int)x->b, (int)y->b);
    }
    for (int k = 0; k < x->b; ++k)
        pa_set(x->a->A, i * x->b + k, pa_get(y->a->A, j * y->b + k));
}
#define _bsetshareblock block_share_setshareblock


static void block_share_setshareblocks(block_share_array x, int is, int ie, block_share_array y, int js) {
    if (is < 0 || is >= x->n) {
        printf("block_share_setblockshares x: n %d is %d\n", x->n, is);
    }
    if (ie > x->n) {
        printf("block_share_setblockshares x: n %d ie %d\n", x->n, ie);
    }
    if (is < 0 || is >= y->n) {
        printf("block_share_setblockshares y: n %d js %d\n", y->n, js);
    }
    if (js + (ie-is) > y->n) {
        printf("block_share_setblockshares y: n %d is %d ie %d js %d\n", y->n, is, ie, js);
    }
    if (x->q != y->q) {
        printf("block_share_setblockshares x->q %d y->q %d\n", x->q, y->q);
    }
    for (int i = 0; i < ie-is; ++i) {
        _bsetshareblock(x, is + i, y, js + i);
    }
}


static void block_share_addpublicblock(block_share_array x, int i, share_t *y) {
    if (i < 0 || i >= x->n) {
        printf("block_share_addpublicblock: n %d i %d\n", block_len(x), i);
    }
    share_t q = block_order(x);
    for (int j = 0; j < block_size(x); ++j) {
        if (_party != 2) {
            pa_set(x->a->A, i * block_size(x) + j, MOD(pa_get(x->a->A, i * block_size(x) + j) + y[j]));
        }
    }
}
#define _baddpublicb block_share_addpublicblock

static void block_share_addpublic(block_share_array x, int i, int j, share_t y) {
    if (i < 0 || i >= x->n) {
        printf("block_share_addpublic n %d i %d\n", x->n, i);
    }
    if (j < 0 || j >= x->b) {
        printf("block_share_addpublic b %d j %d\n", x->b, j);
    }
    share_addpublic(x->a, i * x->b + j, y);
}

static block_share_array block_share_const(int n, int b, share_t v, share_t q) {
    NEWT(block_share_array, ans);
    ans->n = n;
    ans->b = b;
    ans->q = q;
    ans->a = share_const(n*b, v, q);

    return ans;
}
#define _bconst block_share_const

#endif

#endif

