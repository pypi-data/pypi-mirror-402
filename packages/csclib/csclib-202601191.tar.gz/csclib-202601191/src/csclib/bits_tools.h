#ifndef _BITS_TOOLS_H
#define _BITS_TOOLS_H

#include "share_core.h"
#include "share.h"
#include "compare.h"
#include "dshare.h"

// この関数はaes.cの中からコピーしたものなので，二重定義に気をつける．
static void share_xor_bits(_bits x, int i, _bits y, int j)
{
  for (int d=0; d<x->d; d++) {
    share_t xtmp, ytmp;
    xtmp = share_getraw(x->a[d], i);
    ytmp = share_getraw(y->a[d], j);
    xtmp ^= ytmp;
    share_setraw(x->a[d], i, xtmp);
  }
}

static void share_xor_bits2(_bits x, int i, _bits y, int j) {
    for (int d = 0; d < min(x->d, y->d); ++d) {
        share_t xtmp, ytmp;
        xtmp = share_getraw(x->a[d], i);
        ytmp = share_getraw(y->a[d], j);
        xtmp ^= ytmp;
        share_setraw(x->a[d], i, xtmp);
    }
}

// この関数はtreefunction2.hからコピーしたものなので，二重定義に気をつける
_ IfThenElse2(_ c, _ x, _ y) {
    if (c->q != 2) {
        printf("IfThenElse2: c->q = %d\n", c->q);
        exit(1);
    }
    else if (x->q != y->q) {
        printf("IfThenElse2: x->q = %d y->q = %d\n", x->q, y->q);
        exit(1);
    }
    else if (x->n != y->n) {
        printf("IfThenElse2: x->n = %d y->n = %d\n", x->n, y->n);
        exit(1);
    }
    _ c_ = B2A(c, x->q);
    _ dif = vsub(x, y);
    vmul_(dif, c_);
    _ ans = _dup(y);
    vadd_(ans, dif);
    _free(c_);   _free(dif);

    return ans;
}

_ IfThen_b(_ c, _ x) {
    if (c->q != 2) {
        printf("IfThen_b: c->q = %d\n", c->q);
        exit(1);
    }
    _ c_ = B2A(c, x->q);
    _ ans = vmul(x, c_);
    _free(c_);

    return ans;
}

_ IfThen(_ c, _ x) {
    if (c->q != x->q) {
        printf("IfThen: c->q = %d, x->q = %d\n", c->q, x->q);
        exit(1);
    }
    _ ans = vmul(x, c);

    return ans;
}

// TODO: 並列化？
_bits random_bits(int n, int d, share_t q) {
    if (_party > 2) {
        return NULL;
    }

    NEWT(_bits, ans);
    ans->d = d;
    NEWA(ans->a, share_array, d);
    share_t *A;
    NEWA(A, share_t, d);
    
    for (int i = 0; i < d; ++i) {
        if (_party <= 0) {
            for (int j = 0; j < n; ++j) {
                A[j] = RANDOM0(q);
            }
        }
        ans->a[i] = share_new(n, q, A);
    }

    free(A);

    return ans;
}

/////////////////////////////////////////////////////////////
// share_array の連結
/////////////////////////////////////////////////////////////
share_array serialize_share_arrays(int l, share_array *x) {
    int n = len(x[0]);
    share_t q = order(x[0]);
    share_array ans = share_const(l * n, 0, q);
    for (int i = 0; i < l; ++i) {
        for (int j = 0; j < n; ++j) {
            share_setshare(ans, n * i, x[i], j);
        }
    }
    return ans;
}

/////////////////////////////////////////////////////////////
// abc => aaabbbccc (l個ずつコピー)
/////////////////////////////////////////////////////////////
share_array extend_share_array_offset(int l, share_array x, int offset, share_t diff) 
{
  int n = len(x);
  share_t q = order(x);
  share_array ans = share_const(n * l, 0, q);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_x = pa_iter_pos_new(x->A, offset);
  for (int i = 0; i < n; ++i) {
    share_t z = pa_iter_get(itr_x);
    z = (z + diff) % q;
    for (int j = 0; j < l; ++j) {
      //share_setshare(ans, l * i + j, x, i);
      pa_iter_set(itr_ans, z);
    }
    if ((offset > 0) && (i + offset + 1 == n)) {
      pa_iter_free(itr_x);
      itr_x = pa_iter_new(x->A);
    }
  }
  pa_iter_flush(itr_ans);
  pa_iter_free(itr_x);
    
  return ans;
}
#define extend_share_array(l, x) extend_share_array_offset(l, x, 0, 0)

/////////////////////////////////////////////////////////////
// abc => abcabcabc (l 回コピー)
/////////////////////////////////////////////////////////////
share_array extend_cyclic_share_array_offset(int l, share_array x, int offset, share_t diff) 
{
  int n = len(x);
  share_t q = order(x);
  share_array ans = share_const(n * l, 0, q);
  pa_iter itr_ans = pa_iter_new(ans->A);
  for (int j = 0; j < l; ++j) {
    pa_iter itr_x = pa_iter_new(x->A);
    for (int i = 0; i < n; ++i) {
      share_t z = pa_iter_get(itr_x);
      z = (z + diff) % q;
      pa_iter_set(itr_ans, z);
      if ((offset > 0) && (i + offset + 1 == n)) {
        pa_iter_free(itr_x);
        itr_x = pa_iter_new(x->A);
      }
    }
    pa_iter_free(itr_x);
  }
  pa_iter_flush(itr_ans);
    
  return ans;
}
#define extend_cyclic_share_array(l, x) extend_cyclic_share_array_offset(l, x, 0, 0)


///////////////////////////////////////////////////////////////////////
// x の連続する l 個の要素を各桁とする値を n/l 個作る．
///////////////////////////////////////////////////////////////////////
_bits vextend_share_array(int l, share_array x) 
{
  int n = len(x);
  int m = n/l;
  if (m*l != n) {
    printf("vextend_share_array: n = %d l = %d\n", n, l);
    exit(1);
  }
  share_t q = order(x);
  _bits ans = share_const_bits(m, 0, q, l);
  pa_iter *itr_ans;
  NEWA(itr_ans, pa_iter, l);
  for (int i=0; i<l; i++) {
    itr_ans[i] = pa_iter_new(ans->a[i]->A);
  }
  pa_iter itr_x = pa_iter_new(x->A);
  for (int i = 0; i < m; ++i) {
    for (int j = 0; j < l; j++) {
      pa_iter_set(itr_ans[j], pa_iter_get(itr_x));
    }
  }
  for (int i=0; i<l; i++) {
    pa_iter_flush(itr_ans[i]);
  }
  free(itr_ans);
  pa_iter_free(itr_x);
    
  return ans;
}

_bits share_bits_new(int d, int n, share_t q, share_t *A) {
    share_t *A_bits;

    NEWT(_bits, ans);
    ans->d = d;
    NEWA(ans->a, share_array, n);
    if (_party <= 0) {
        NEWA(A_bits, share_t, n);

        for (int j = 0; j < d; ++j) {
            for (int i = 0; i < n; ++i) {
                A_bits[i] = (A[i]>>j) & 1;
            }
            ans->a[j] = share_new(n, q, A_bits);
        }

        free(A_bits);
    } else if (1 <= _party && _party <= 2) {
        for (int j = 0; j < d; ++j) {
            ans->a[j] = share_new(n, q, A_bits);
        }
    }

    return ans;
}

_bits share_bits_const(int d, int n, share_t q, share_t x) {
    share_t *x_bits;
    NEWA(x_bits, share_t, d);
    for (int i = 0; i < d; ++i) {
        x_bits[i] = (x>>i) & 1;
    }

    NEWT(_bits, b);
    b->d = d;
    NEWA(b->a, share_array, d);
    for (int j = 0; j < d; ++j) {
        b->a[j] = share_const(n, 0, q);
        //pa_iter_new(b->a[j]->A);
    }

#if 0
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < d; ++j) {
            share_setpublic(b->a[j], i, x_bits[j]); 
        }
    }
#else
    if (_party <= 1) {
      for (int j = 0; j < d; ++j) {
        pa_iter itr = pa_iter_new(b->a[j]->A);
        for (int i = 0; i < n; ++i) {
          //pa_iter_set(b->a[j]->A, x_bits[j]);
          pa_iter_set(itr, x_bits[j]);
        }
        //pa_iter_flush(b->a[j]->A);
        pa_iter_flush(itr);
      }
    }
#endif
    free(x_bits);

    return b;
}

//////////////////////////////////////////////////////////////////
// x の連続する l 個の和を求める
//////////////////////////////////////////////////////////////////
share_array extended_sum(int l, share_array x) {
    int n = len(x);
    share_t q = order(x);
    if (n % l != 0) {
        printf("extended_sum    n = %d, l = %d, n %% l = %d\n", n, l, n % l);
        exit(1);
    }

    share_array ans = share_const(l, 0, q);
    for (int i = 0; i < n / l; ++i) {
        for (int j = 0; j < l; ++j) {
            share_addshare(ans, j, x, i * l + j);
        }
    }

    return ans;
}

_bits extended_total_xor_bits(int l, _bits x) {
    int n = len(x->a[0]);
    int d = x->d;
    int q = order(x->a[0]);
    if (n % l != 0) {
        printf("extended_total_xor_bits n = %d  l = %d  n %% l = %d\n", n, l, n % l);
        exit(1);
    }
    _bits ans = share_bits_const(d, l, q, 0);
    for (int i = 0; i < n / l; ++i) {
        for (int j = 0; j < l; ++j) {
            share_xor_bits(ans, j, x, i * l + j);
        }
    }

    return ans;
}




void share_setshares_bits(_bits x, int si, int ei, _bits y, int j) {
    if (x->d != y->d) {
        printf("share_setshres_bits x->d: %d    y->d: %d\n", x->d, y->d);
        exit(1);
    }
    if (order(x->a[0]) != order(y->a[0])) {
        printf("share_setshraes_bits: order(x->a[0]): %d    order(y->a[0]): %d\n", order(x->a[0]), order(y->a[0]));
        exit(1);
    }
    if (si > ei || si < 0 || ei > len(x->a[0])) {
        printf("share_setshares_bits si: %d ei: %d\n", si, ei);
        exit(1);
    }
    if (j + ei - si > len(y->a[0])) {
        printf("share_setshre_bits  si: %d  ei: %d  j: %d   len(y->a[0]): %d\n", si, ei, j, len(y->a[0]));
        exit(1);
    }

    for (int i = 0; i < ei - si; ++i) {
        share_setshare_bits(x, si + i, y, j + i);
    }
}

_bits share_reconstruct_bits_channel(_bits x, int channel) {
    if (_party > 2) {
        return NULL;
    }
    if (x == NULL) {
        return NULL;
    }

    int n = len(x->a[0]);
    int d = x->d;
    share_t q = order(x->a[0]);
    _bits ans = share_bits_const(d, n, q, 0);
    if (_party == 0) {
        share_setshares_bits(ans, 0, n, x, 0);
    }
    else {
        for (int k = 0; k < d; ++k) {   // TODO: ここを並列化
            mpc_exchange_channel(x->a[k]->A->B, ans->a[k]->A->B, pa_size(x->a[k]->A), channel);
            vadd_(ans->a[k], x->a[k]);
        }
    }

    return ans;
}

share_array serialize_bits(_bits x) {
    int d = x->d;
    int n = len(x->a[0]);
    share_t q = order(x->a[0]);
    share_array ans = share_const(d * n, 0, q);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < d; ++j) {
            share_setshare(ans, i * d + j, x->a[j], i);
        }
    }
    return ans;
}

_ IfThenElse_channel(_ f, _ a, _ b, int channel);

_bits IfThenElse_bits_channel(share_array e, _bits x, _bits y, int channel) {
    int n = len(x->a[0]);
    int q = order(x->a[0]);

    share_array serialized_x = serialize_bits(x);
    share_array serialized_y = serialize_bits(y);
    share_array extended_e = extend_share_array(x->d, e);

    share_array serialized_ans = IfThenElse_channel(extended_e, serialized_x, serialized_y, channel);

    _bits ans = share_bits_const(x->d, n, q, 0);
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < x->d; ++k) {
            share_setshare(ans->a[k], i, serialized_ans, x->d * i + k);
        }
    }

    share_free(serialized_x);
    share_free(serialized_y);
    share_free(extended_e);
    share_free(serialized_ans);

    // _print_bits(ans);

    return ans;
}

_bits IfThenElse2_bits(share_array e, _bits x, _bits y) {
    int n = len(x->a[0]);
    int q = order(x->a[0]);

    share_array serialized_x = serialize_bits(x);
    share_array serialized_y = serialize_bits(y);
    share_array extended_e = extend_share_array(x->d, e);

    share_array serialized_ans = IfThenElse2(extended_e, serialized_x, serialized_y);

    _bits ans = share_bits_const(x->d, n, q, 0);
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < x->d; ++k) {
            share_setshare(ans->a[k], i, serialized_ans, x->d * i + k);
        }
    }

    share_free(serialized_x);
    share_free(serialized_y);
    share_free(extended_e);
    share_free(serialized_ans);

    // _print_bits(ans);

    return ans;
}

_bits IfThen_b_bits(share_array e, _bits x) {
    int n = len(x->a[0]);
    int q = order(x->a[0]);

    share_array serialized_x = serialize_bits(x);
    share_array extended_e = extend_share_array(x->d, e);

    share_array serialized_ans = IfThen_b(extended_e, serialized_x);

    _bits ans = share_bits_const(x->d, n, q, 0);
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < x->d; ++k) {
            share_setshare(ans->a[k], i, serialized_ans, x->d * i + k);
        }
    }

    share_free(serialized_x);
    share_free(extended_e);
    share_free(serialized_ans);

    // _print_bits(ans);

    return ans;
}

void bits_free(_bits x) {
    for (int i = 0; i < x->d; ++i)
        share_free(x->a[i]);
    free(x->a);
    free(x);
}

void _move_bits(_bits x, _bits y) {
    if (x == NULL)  return;
    if (y == NULL)  return;
    for (int i = 0; i < x->d; ++i) {
        share_free(x->a[i]);
    }
    free(x->a);
    *x = *y;
    free(y);
}

_bits vsub_bits(_bits x, _bits y) {
    if (len(x->a[0]) != len(y->a[0])) {
        printf("vsub_bits: len(x->a[0]) %d  len(y->a[0]) %d\n", len(x->a[0]), len(y->a[0]));
        exit(1);
    }
    if (x->d != y->d) {
        printf("vsub_bits: x->d %d  y->d %d\n", x->d, y->d);
        exit(1);
    }
    if (order(x->a[0]) != 2) {
        printf("total_xor_bits order(x->a[0]): %d\n", order(x->a[0]));
        exit(1);
    }
    if (order(y->a[0]) != 2) {
        printf("total_xor_bits order(y->a[0]): %d\n", order(y->a[0]));
        exit(1);
    }
    
    int n = len(x->a[0]);
    int d = x->d;
    _bits z = share_const_bits(n, 0, 2, d);
    share_setshares_bits(z, 0, n, x, 0);
    for (int i = 0; i < n; ++i) {
        share_xor_bits(z, i, y, i);
    }

    return z;
}

void vsub_bits_(_bits x, _bits y) {
    _bits tmp = vsub_bits(x, y);
    _move_bits(x, tmp);
}

_bits total_xor_bits(_bits x) {
    // _print_bits(x);
    if (order(x->a[0]) != 2) {
        printf("total_xor_bits order(x->a[0]): %d\n", order(x->a[0]));
        exit(1);
    }
    int n = len(x->a[0]);
    int d = x->d;

    _bits y = share_const_bits(1, 0, 2, d);
    // printf("y\n");
    // _print_bits(y);
    // printf("x\n");
    // _print_bits(x);
    for (int i = 0; i < n; ++i) {
        share_xor_bits(y, 0, x, i);
    }

    return y;
}

#ifndef AppPerm_bits_channel
 #define AppPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 0, channel)
 static _bits AppPerm_bits_bd_channel(_bits x, _ sigma, int inverse, int channel);
#endif

#ifndef AppInvPerm_bits_channel
 #define AppInvPerm_bits_channel(a, sigma, channel) AppPerm_bits_bd_channel(a, sigma, 1, channel)
 static _bits AppPerm_bits_bd_channel(_bits x, _ sigma, int inverse, int channel);
#endif

void AppPerm_bits_channel_(_bits x, share_array sigma, int channel) {
    _bits tmp = AppPerm_bits_channel(x, sigma, channel);
    _move_bits(x, tmp);
}

void AppInvPerm_bits_channel_(_bits x, share_array sigma, int channel) {
    _bits tmp = AppInvPerm_bits_channel(x, sigma, channel);
    _move_bits(x, tmp);
}

#endif