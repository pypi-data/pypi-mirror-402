#ifndef _BP_H
#define _BP_H

#include <stdio.h>
#include <stdlib.h>

#include "share.h"
// #include "LOUDS.h"

/************************************************************************************************
約束事
１：BP bは位数2を想定する．
２：excessやdepthなどの位数は、基本的に2n以上の最小の２冪とする(nは木のノード数で，len(b)=2nである)．
３：計算結果(nextsiblingやprevsiblingなど)のインデックスを0-indexedにするのか1-indexedにするのか決めた方が良い．
　　今のところ"LOUDS.h"に合わせて0-indexedにしている.
************************************************************************************************/




/************************************************************************************************
プロトタイプ宣言．postorderなど，他の関数でよく使われる関数の宣言だけ済ませておく．
************************************************************************************************/
_ BP_levelorder(_);
_ BP_postorder(_);
_ BPtoLOUDS(_);
_ BP_treesum(_, _);






/************************************************************************************************
以下，関数定義
************************************************************************************************/

#if 0
_ IfThen2(_ c, _ x) {
    if (c->q != 2) {
        printf("IfThen2: c->q = %d\n", c->q);
        exit(1);
    }
    _ c_ = B2A(c, x->q);
    _ ans = vmul(c_, x);
    _free(c_);

    return ans;
}


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
#endif

// share_coreにでも追加するとよさそう。
// 入力のshare_arrayの順番を逆転させたものを返す。
_ share_reverse(share_array a) {
    int n = len(a);
    _ ans = _dup(a);
    for (int i = 0; i < n; ++i) {
        pa_set(ans->A, i, pa_get(a->A, n-1-i));
    }
    return ans;
}
#define _reverse share_reverse


void share_reverse_(share_array a) {
    share_array ans = share_reverse(a);
    _move_(a, ans);
}
#define reverse_ share_reverse_


/************************************************************************************************
BP_excess
input:
    b: 入力木のBP表現
output:
    e: 各括弧のexcess
備考
    eの位数は2n以上の最小の２冪．
    定数ラウンド．
    チェック済み
************************************************************************************************/
_ BP_excess(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ b_q = _dup(b);
    B2A_(b_q, q);
    _ idx = Perm_ID2(2*n, q);
    for (int i = 0; i < 2*n; ++i)
        _addpublic(idx, i, 1);
    _ b_pre_sum = PrefixSum(b_q);
    smul_(2, b_pre_sum);
    _ e = _vsub(idx, b_pre_sum);
    _free(b_q);
    _free(idx);
    _free(b_pre_sum);

    return e;
}


/************************************************************************************************
BP_depth
input:
    b: 入力のBP表現
output:
    d: 各ノードの深さ（preorder順）
note:
    dの位数は2n以上の最小の２冪
    定数ラウンド
    チェック済み
************************************************************************************************/
_ BP_depth(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ e = BP_excess(b);
    _ sigma = StableSort2(b);
    _ tmp = AppInvPerm(e,sigma);
    _ d = _slice(tmp, 0, n);
    _free(e);
    _free(sigma);
    _free(tmp);

    return d;
}


/************************************************************************************************
BP_isroot
input:
    b: BP表現
output:
    c: c[i]==1の時，ノードiは根．
note:
    cは位数２
    チェック済み
************************************************************************************************/
_ BP_isroot(_ b) {
    int n = len(b)/2;
    _ d = BP_depth(b);
    _ ones = _const(n, 1, order(d));
    _ c = Equality(d, ones);
    _free(d);
    _free(ones);

    return c;
}


/************************************************************************************************
BP_isleaf
input:
    b: BP表現
output:
    z: z[i]==1の時，ノードiは葉
note:
    zは位数２．
    チェック済み
************************************************************************************************/
_ BP_isleaf(_ b) {
    int n = len(b)/2;
    _ sigma = StableSort2(b);
    _ c = _dup(b);
    for (int i = 0; i < 2*n-1; ++i)
        _addshare(c, i, b, i+1);
    _setpublic(c, 2*n-1, 0);
    _ v = AppInvPerm(c, sigma);
    _ z = _slice(v, 0, n);

    _free(sigma);
    _free(c);
    _free(v);

    return z;
}


/************************************************************************************************
BP_isfirstchild
input:
    b: BP表現
output:
    c: c[i]==1の時，ノードiは最初の子
note:
    cの位数は２．
    チェック済み
************************************************************************************************/
_ BP_isfirstchild(_ b) {
    int n = len(b)/2;
    _ sigma = StableSort2(b);
    _ x = vneg(b);
    _ y = rshift(x, 1);
    _ z = vmul(x, y);
    _ w = AppInvPerm(z, sigma);
    _ c = _slice(w, 0, n);
    _free(x);
    _free(y);
    _free(z);
    _free(w);
    _free(sigma);

    return c;
}


/************************************************************************************************
BP_islastchild
input:
    b: BP 表現
output:
    c: c[i]==1の時，ノードiは最後の子
note:
    cの位数は２．
    check済
************************************************************************************************/
_ BP_islastchild(_ b) {
    int n = len(b)/2;
    _ b_r = share_reverse(b);
    vneg_(b_r);
    _ c = BP_isfirstchild(b_r);
    // printf("c:  "); _print(c);
    share_reverse_(c);
    _ p = BP_postorder(b);
    // printf("p:  "); _print(p);
    AppPerm_(c, p);
    _free(b_r);
    _free(p);

    return c;
}


/************************************************************************************************
BP_isleftmost
input:
    b: BP expression
output:
    c: c[i]==1の時，ノードiは（自分と同じ深さのノードの中で）一番左．
note:
    cの位数は２．
************************************************************************************************/
_ BP_isleftmost(_ b) {
    int n = len(b) / 2;
    _ e = BP_excess(b);
    _pair p = share_radix_sort(e);
    _ sigma = p.y;
    _ t = AppPerm(b, sigma);
    _ t_r = rshift(t, 0);
    _ c = XOR(t, t_r);
    AppInvPerm_(c, sigma);
    _ rho = StableSort2(b);
    AppInvPerm_(c, rho);
    _slice_(c, 0, n);

    _free(e);
    _free(p.x); _free(p.y);
    _free(t);
    _free(t_r);
    _free(rho);

    return c;
}


/************************************************************************************************
BP_levelorder (BP_levelrank)
input:
    b: BP expression
output:
    l: l[i]はノードiのlevel rank
note:
    lの位数は2n以上の最小の２冪．
    log ラウンド
    チェック済み
************************************************************************************************/
_ BP_levelorder(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ rho = StableSort2(b);
    _ pi = BPtoLOUDS(b);
    _ s = AppPerm(b, pi);
    _ sigma = StableSort2(s);
    _ tau_ = AppInvPerm(sigma, pi);
    _ tau = AppInvPerm(tau_, rho);
    _ l = _slice(tau, 0, n);

    _free(rho);
    _free(pi);
    _free(s);
    _free(sigma);
    _free(tau_);
    _free(tau);

    return l;
}


/************************************************************************************************
BP_degree
input:
    b: BP expression
output:
    z: z[i]はノードiの子の個数
note:
    zの位数は2n以上の最小の２冪.
    logラウンド
    うまく動かない．GroupSumを見直す必要あり．
************************************************************************************************/
_ BP_degree(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ pi = BPtoLOUDS(b);
    _ g = AppPerm(b, pi);
    share_insert_head_(g, 1);
    //printf("g:");   _print(g);
    _ g_neg = vneg(g);
    

    B2A_(g_neg, q);
    _ g2 = B2A(g, q);
    //printf("g_neg:");   _print(g_neg);    
    _ w = GroupSum(g2, g_neg);
    //printf("w:");   _print(w);
    _slice_(w, 1, 2*n+1);
    AppInvPerm_(w, pi);
    _ sigma = StableSort2(b);
    _ z = AppInvPerm(w, sigma);
    _slice_(z, 0, n);
    

    _free(pi);
    _free(g);
    _free(g_neg);
    _free(w);
    _free(sigma);
    _free(g2);

    return z;
}


/************************************************************************************************
BP_parentlabel
input:
    b: BP
    v: label
output:
    z:
note:
    チェック済み
************************************************************************************************/
_ BP_parentlabel(_ b, _ v) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ pi = BPtoLOUDS(b);
    _ rho = StableSort2(b);
    _ post = BP_postorder(b);
    _ zeros = _const(n, 0, order(v));
    _ u = AppInvPerm(v, post);
    _ w = _concat(zeros, u);
    // printf("w:");   _print(w);
    _ g = AppPerm(b, pi);
    AppPerm_(w, rho);
    AppPerm_(w, pi);
    // printf("w:");   _print(w);
    _insert_head_(g, 1);
    _insert_head_(w, 0);
    // printf("g:");   _print(g);
    // printf("w:");   _print(w);
    _ x = Propagate2(g, w);
    _slice_(x, 1, 2*n+1);
    AppInvPerm_(x, pi);
    // printf("x:");   _print(x);
    AppInvPerm_(x, rho);
    _ z = _slice(x, 0, n);

    _free(pi);
    _free(post);
    _free(zeros);
    _free(u);
    _free(w);
    _free(g);
    _free(x);
    _free(rho);

    return z;
}


/************************************************************************************************
BP_parent
input:
    b: BP expression
output:
    z: z[i]はノードiの親の番号
note:
    zの位数は2n以上の最小の２冪．
    チェック済み
************************************************************************************************/
_ BP_parent(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ z = BP_parentlabel(b, v);
    _free(v);

    return z;
}


_ BP_firstchildlabel(_ b, _ v) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ sigma = StableSort2(b);
    _ zeros = _const(n, 0, order(v));
    _ u = _concat(v, zeros);
    AppPerm_(u, sigma);
    lshift_(u, 0);
    AppInvPerm_(u, sigma);
    _slice_(u, 0, n);
    _ f = BP_isleaf(b);
    vneg_(f);
    _ z = IfThen_b(f, u);

    _free(sigma);
    _free(zeros);
    _free(u);
    _free(f);
    
    return z;
} 


/************************************************************************************************
BP_firstchild
input:
    b: BP
output:
    z: firstchildの番号
note:
    子供の番号は１index. 子供がいないノードの返り値は０以外の何かにした方がいいかも．（参考：nextsiblinglabel）
    チェック済み
************************************************************************************************/
_ BP_firstchild(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ z = BP_firstchildlabel(b, v);

    _free(v);

    return z;
}


/************************************************************************************************
BP_lastchildlabel
input:
    b: BP
    v: label
output:
    z: 最後の子供のラベル
note:
    チェック済み
************************************************************************************************/
_ BP_lastchildlabel(_ b, _ v) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ p = BP_postorder(b);
    _ v_r = AppInvPerm(v, p);
    share_reverse_(v_r);
    _ b_r = _dup(b);
    share_reverse_(b_r);
    vneg_(b_r);

    _ w = BP_firstchildlabel(b_r, v_r);
    share_reverse_(w);
    // printf("w:");   _print(w);
    _ z = AppPerm(w, p);

    _free(v_r);
    _free(b_r);
    _free(w);
    _free(p);

    return z;
}


/************************************************************************************************
BP_lastchild
input:
    b: BP
output:
    z: last childのノード番号
note:
    チェック済み
************************************************************************************************/
_ BP_lastchild(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ z = BP_lastchildlabel(b, v);

    _free(v);

    return z;
}


/************************************************************************************************
BP_preorder (prerank)
input:
    b: BP expression
output:
    p: preorder
note:
    constant rounds
************************************************************************************************/
_ BP_preorder(_ b) {
    int n = len(b), k = blog(2*n-1)+1, q = 1<<k;
    _ p = Perm_ID2(n, q);
    return p;
}


/************************************************************************************************
BP_postorder
input:
    b:
output:
    p: postorder
note:
    log rounds
    チェック済み
************************************************************************************************/
_ BP_postorder(_ b) {
    int n = len(b)/2, q;
    _ rho = StableSort2(b);
    //printf("rho: ");    _print(rho);
    _ pi = BPtoLOUDS(b);
    //printf("pi: "); _print(pi);
    _ s = AppPerm(b, pi);
    //printf("s:   ");    _print(s);
    _ sigma = StableSort2(s);
    //printf("sigma:   ");    _print(sigma);
    _ tau_ = AppInvPerm(sigma, pi);
    //printf("tau_:   ");    _print(tau_);
    _ tau = AppInvPerm(tau_, rho);
    //printf("tau:   ");    _print(tau);
    _ l = _slice(tau, 0, n);
    //printf("l:   ");    _print(l);
    _ r = _slice(tau, n, 2*n);
    //printf("r:   ");    _print(r);
    q = order(r);
    for (int i = 0; i < n; ++i)
        _addpublic(r, i, q-n);
    //printf("r:   ");    _print(r);
    _ id = Perm_ID2(n, order(r));
    //printf("id:   ");    _print(id);
    _ p = AppInvPerm(id, r);
    //printf("p::::"); _print(p);
    AppPerm_(p, l);

    _free(rho);
    _free(pi);
    _free(s);
    _free(sigma);
    _free(tau_);
    _free(tau);
    _free(l);
    _free(r);
    _free(id);

    return p;
}


/************************************************************************************************
BP_desc
input:
    b: BP
output:
    z: size of each node
note:
    実際のサイズの２倍になっていることに注意．
    チェック済み
************************************************************************************************/
_ BP_desc(_ b) {
    int n = len(b) / 2, k = blog(2*n-1)+1, q = 1<<k;
    _ p = BP_postorder(b);
    _ idx = Perm_ID2(2*n, q);
    _ sigma = StableSort2(b);
    _ pos = AppInvPerm(idx, sigma);
    _ op = _slice(pos, 0, n);
    _ cl = _slice(pos, n, 2*n);
    AppPerm_(cl, p);
    
    _ z = vsub(cl, op);
    for (int i = 0; i < n; ++i)
        _addpublic(z, i, 1);

    _free(idx);
    _free(sigma);
    _free(pos);
    _free(op); 
    _free(cl);
    _free(p);

    return z;
}


/************************************************************************************************
BP_leftmostleaflabel
input:
    b: BP
output:
    v: label
note:
    チェック済み
************************************************************************************************/
_ BP_leftmostleaflabel(_ b, _ v) {
    _ f = BP_isleaf(b);
    _ g = share_reverse(f);
    // printf("g:");   _print(g);
    _ w = share_reverse(v);
    // printf("w:");   _print(w);
    _ y = Propagate2(g, w);
    // printf("y:");   _print(y);
    reverse_(y);

    _free(f);
    _free(g);
    _free(w);

    return y;
}


/************************************************************************************************
BP_leftmostleaf
input:
    b: BP
output:
    z: left most leafのノード番号(0 indexed)
note:
    チェック済み
************************************************************************************************/
_ BP_leftmostleaf(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ z = BP_leftmostleaflabel(b, v);
    _free(v);

    return z;
}


/************************************************************************************************

input:
    
output:
    
note:
    チェック済み
************************************************************************************************/
_ BP_rightmostleaflabel(_ b, _ v) {
    _ b_r = share_reverse(b);
    vneg_(b_r);
    _ p = BP_postorder(b);
    _ v_r = AppInvPerm(v, p);
    share_reverse_(v_r);
    _ z = BP_leftmostleaflabel(b_r, v_r);
    share_reverse_(z);
    AppPerm_(z, p);

    _free(b_r);
    _free(v_r);
    _free(p);

    return z;
}


/************************************************************************************************
BP_rightmostleaf
input:
    b: BP
output:
    z: the number of right most leaf
note:
    チェック済み
************************************************************************************************/
_ BP_rightmostleaf(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ z = BP_rightmostleaflabel(b, v);
    _free(v);

    return z;
}


/************************************************************************************************
BP_childrank
input:
    b: BP
output:
    z: z_iはnode iが兄弟の中で何番目か
note:
    group prefix sumが必要？
************************************************************************************************/
_ BP_childrank(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ pi = BPtoLOUDS(b);
    _ t = AppPerm(b, pi);
    //_ sigma = StableSort2(t);
    _ id = Perm_ID2(2*n, q);
    share_insert_head_(t, 1);
    share_insert_head_(id, 0);
    _ x = Propagate2(t, id);
    _ s = vsub(id, x);
    _ sigma = StableSort2(t);
    AppInvPerm_(s, sigma);
    _ rho = StableSort2(b);
    s = _slice(s, 0, n*2);
    _ z = AppInvPerm(s, rho);
    //_ z = _slice(s, 0, n);

    _free(pi);
    _free(t);
    _free(sigma);
    _free(id);
    _free(x);
    _free(s);
    _free(rho);

    return z;
}


/************************************************************************************************
BP_nextsiglinglabel
input:
    b: BP
    v: label
    r: a element of R
output:
    z: z_i = v_j if the next sibling node j of node i exists, and z_i = r otherwise.
note:
    r の長さは１．
    チェック済み
************************************************************************************************/
_ BP_nextsiblinglabel(_ b, _ v, _ r) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ pi = BPtoLOUDS(b);
    _ rho = StableSort2(b);
    _ rs = _const(n, 0, order(v));
    for (int i = 0; i < n; ++i)
        _setshare(rs, i, r, 0);
    _ u = _concat(v, rs);
    //printf("u:");   _print(u);
    AppPerm_(u, rho);
    AppPerm_(u, pi);
    //printf("u:");   _print(u);
    lshift_(u, 0);
    _setshare(u, 2*n-1, r, 0);
    AppInvPerm_(u, pi);
    AppInvPerm_(u, rho);
    _ z = _slice(u, 0, n);
    
    _free(pi);
    
    _free(rho);
    
    //printf("ok\n");
    _free(rs);
    _free(u);

    return z;
}


/************************************************************************************************
BP_nextsibling
input:
    b: BP
output:
    z: nextsibling node number
note:
    チェック済み
************************************************************************************************/
_ BP_nextsibling(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ r = _const(1, 0, q);
    _ z = BP_nextsiblinglabel(b, v, r);

    _free(v);
    _free(r);

    return z;
}   


/************************************************************************************************
BP_prevsiblinglabel
input:
    b: BP
    v: label
    r: dummy label
output:
    z: previous sibling node label
note:
    チェック済み
************************************************************************************************/
_ BP_prevsiblinglabel(_ b, _ v, _ r) {
    _ b_r = share_reverse(b);
    vneg_(b_r);
    _ p = BP_postorder(b);
    _ v_r = AppInvPerm(v, p);
    share_reverse_(v_r);
    _ z = BP_nextsiblinglabel(b_r, v_r, r);
    share_reverse_(z);
    AppPerm_(z, p);

    _free(b_r);
    _free(v_r);
    _free(p);

    return z;
}


/************************************************************************************************
BP_prevsibling
input:
    b: BP
output:
    z: previous sibling node number
note:
    チェック済み
************************************************************************************************/
_ BP_prevsibling(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ r = _const(1, 0, q);
    _ z = BP_prevsiblinglabel(b, v, r);

    _free(v);
    _free(r);

    return z;
}


/************************************************************************************************
BP_numleavs
input:
    b: BP
output:
    z: the number of leaves under node i
note:
    チェック済み
************************************************************************************************/
_ BP_numleaves(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ f = BP_isleaf(b);
    B2A_(f, q);
    _ z = BP_treesum(b, f);

    _free(f);

    return z;
}


/************************************************************************************************
BP_leafrank
input:
    b: BP
output:
    z: z_i = the number of leaves to the left of node i.
note:
    自分が葉の時には，勘定に自身も含める．
    チェック済み
************************************************************************************************/
_ BP_leafrank(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ f = BP_isleaf(b);
    B2A_(f, q);
    _ z = PrefixSum(f);

    _free(f);

    return z;
}


/************************************************************************************************
BP_levelnextlabel
input:
    b: BP
    v: label
    r: dummby label
output:
    z: 
note:
    チェック済み
************************************************************************************************/
_ BP_levelnextlabel(_ b, _ v, _ r) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ d = BP_depth(b);
    _pair p = share_radix_sort(d);
    _ sigma = p.y;
    _ sorted_d = p.x;
    // printf("sorted_d:");    _print(sorted_d);
    _ sorted_v = AppPerm(v, sigma);
    // printf("sorted_v:");    _print(sorted_v);
    _ lshifted_sorted_v = lshift(sorted_v, 0);
    _ lshifted_sorted_d = lshift(sorted_d, 0);
    _ c = Equality(sorted_d, lshifted_sorted_d);
    // printf("c:");   _print(c);
    _ rs = _const(n, 0, order(v));
    for (int i = 0; i < n; ++i)
        _setshare(rs, i, r, 0);
    // printf("rs:");  _print(rs);
    _ z = IfThenElse2(c, lshifted_sorted_v, rs);
    AppInvPerm_(z, sigma);

    _free(d);
    _free(p.x); _free(p.y);
    _free(sorted_v);
    _free(lshifted_sorted_d);
    _free(lshifted_sorted_v);
    _free(c);
    _free(rs);
    
    return z;
}


/************************************************************************************************

input:
    
output:
    
note:
    チェック済み
************************************************************************************************/
_ BP_levelnext(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ r = _const(1, 0, q);
    _ z = BP_levelnextlabel(b, v, r);

    _free(v);
    _free(r);

    return z;
}


/************************************************************************************************

input:
    
output:
    
note:
    チェック済み
************************************************************************************************/
_ BP_levelprevlabel(_ b, _ v, _ r) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ d = BP_depth(b);
    _pair p = share_radix_sort(d);
    _ sigma = p.y;
    _ sorted_d = p.x;
    _ sorted_v = AppPerm(v, sigma);
    _ rshifted_sorted_v = rshift(sorted_v, 0);
    _ rshifted_sorted_d = rshift(sorted_d, 0);
    _ c = Equality(sorted_d, rshifted_sorted_d);
    _ rs = _const(n, 0, order(v));
    for (int i = 0; i < n; ++i)
        _setshare(rs, i, r, 0);
    _ z = IfThenElse2(c, rshifted_sorted_v, rs);
    AppInvPerm_(z, sigma);

    _free(d);
    _free(p.x); _free(p.y);
    
    _free(sorted_v);
    _free(rshifted_sorted_d);
    _free(rshifted_sorted_v);
    _free(c);
    _free(rs);
    
    return z;
}


/************************************************************************************************

input:
    
output:
    
note:
    チェック済み．ノード番号は0-indexed
************************************************************************************************/
_ BP_levelprev(_ b) {
    int n = len(b)/2, k = blog(2*n-1)+1, q = 1<<k;
    _ v = Perm_ID2(n, q);
    _ r = _const(1, 0, q);
    _ z = BP_levelprevlabel(b, v, r);

    _free(v);
    _free(r);

    return z;
}


/************************************************************************************************
BP_pathsum
input:
    b: BP
    v: label
output:
    s: pathsum
note:
    各share_arrayの位数をもう少し考えた方がいいかも．sigmaの位数とか
************************************************************************************************/
_ BP_pathsum(_ b, _ v) {
    int n = len(b)/2;
    _ p = BP_postorder(b);
    
    _ u = AppInvPerm(v, p);
    // printf("u");    _print(u);
    _ sigma = StableSort2(b);
    // printf("u:");   _print(u);
    // return sigma;
    smul_(order(v)-1, u);
    _ w = _concat(v, u);
    // printf("w:");   _print(w);
    AppPerm_(w, sigma);
    // printf("w:");   _print(w);
    _ x = PrefixSum(w);
    // _print(x);
    _ z = AppInvPerm(x, sigma);
    _ s = _slice(z, 0, n);
    _free(u);   _free(sigma);
    _free(w);   _free(x);
    _free(z);
    _free(p);

    return s;
}


/************************************************************************************************
BP_treesum
input:
    b: BP
    v: label
output:
    s: treesum
note:
    こっちも位数を気にした方がいいかもしれない．
************************************************************************************************/
_ BP_treesum(_ b, _ v) {
    int n = len(b)/2;
    _ sigma = StableSort2(b);
    // printf("ok\n");
    _ zeros = _const(n, 0, order(v));
    _ tmp = _concat(v, zeros);
    _ w = AppPerm(tmp, sigma);
    _free(tmp);
    // printf("ok2\n");
    _ u = PrefixSum(w);
    // printf("ok3\n");
    _ x = AppInvPerm(u, sigma);
    _ p = BP_postorder(b);
    _ y = _slice(x, n, 2*n);
    _ z = AppPerm(y, p);
    _ s = _vadd(v, z);
    _slice_(x, 0, n);
    vsub_(s, x);
    _free(sigma);   _free(zeros);
    _free(w);   _free(u);   _free(x);
    _free(y);   _free(z);
    _free(p);

    return s;
}


/************************************************************************************************
BPtoLOUDS
input:
    b: BP
output:
    pi: BPからLOUDSへの置換
note:
    bに対してAppPerm(b, pi)でLOUDSが計算できる．AppInvPermではないことに注意．
************************************************************************************************/
_ BPtoLOUDS(_ b) {
    int n = len(b) / 2;
    _ e = BP_excess(b);
    //printf("e: ");  _print(e);
    _pair p = share_radix_sort(e);  //_pairのメモリ解放について調べること！
    _ sigma = p.y;
    //_print(p.x);
    //printf("sigma: ");  _print(sigma);
    _ id = Perm_ID2(2*n, 2*n);
    _ sigma_inv = AppInvPerm(id, sigma);
    //printf("sigma_inv: ");  _print(sigma_inv);
    _ u = AppPerm(b, sigma);
    //printf("u: ");  _print(u);
    _ rho = StableSort2(u);
    //printf("rho: ");  _print(rho);
    _ tau = _const(2*n, 0, order(sigma));
    for (int i = 0; i < n; ++i) {
        _setpublic(tau, i, n+i);
        _setpublic(tau, n+i, i);
    }
    //printf("tau: ");  _print(tau);
    _ pi = Perm_ID2(2*n, 2*n);
    //_ pi = Perm_ID2(2*n, order(sigma));
    _ tmp = _dup(b);
//    printf("pi0: ");  _print(pi);
    AppPerm_(pi, sigma);
//    pi = AppPerm(pi, sigma);
//    printf("pi1: ");  _print(pi);
    AppPerm_(tmp, sigma);
    //printf("b.sigma: ");    _print(tmp);
    AppInvPerm_(pi, rho);
    AppInvPerm_(tmp, rho);
    //printf("b.sigma.rho^-1:");  _print(tmp);
    AppInvPerm_(pi, tau);
    //printf("b.sigma.rho^-1.tau^-1:");  _print(tmp);
    AppPerm_(pi, rho);
    //printf("b.sigma.rho^-1.tau^-1.rho:");  _print(tmp);
    _free(e);   _free(sigma);
    _free(u);   
    _free(rho); _free(tau);
    _free(tmp);
    _free(sigma_inv);
    _free(id);
    _free(p.x);

    return pi;
}


/***********************************************
levelorderとpostorderを返す。
lがlevelorder、pがpostorderである。
lとpの位数がこのままでいいのかちょっと疑問。
正確には、lとrの位数か。
***********************************************/
_pair BP_levelorder_postorder(_ b) {
    int n = len(b)/2, q;
    _ rho = StableSort2(b);
    _ pi = BPtoLOUDS(b);
    _ s = AppPerm(b, pi);
    _ sigma = StableSort2(s);
    _ tau_ = AppInvPerm(sigma, pi);
    _ tau = AppInvPerm(tau_, rho);
    _ l = _slice(tau, 0, n);
    _ r = _slice(tau, n, 2*n);
    q = order(r);
    for (int i = 0; i < n; ++i)
        _addpublic(r, i, q-n);
    _ id = Perm_ID2(n, order(r));
    _ p = AppInvPerm(id, r);
    AppPerm_(p, l);
    _pair ans = {l, p};
    _free(tau);
    _free(tau_);
    _free(pi);
    _free(rho);
    _free(sigma);
    _free(id);
    _free(r);
    _free(s);
    return ans;
}


/************************************************************************************************
BP_patheval
input:
    b: bP
    c: comparison result
    v: lavel
output:
    z: 決定木評価の計算結果
note:
    正しく動いたはず．
************************************************************************************************/
_ BP_patheval(_ b, _ c_, _ v) {
    int n = len(b)/2;
    int k = blog(2*n-1)+1;
    _ c = B2A(c_, 1<<k);
    _ s = BP_pathsum(b, c);
    //printf("s:");   _print(s);
    _ d = BP_depth(b);
    //printf("d:");   _print(d);
    _ l = BP_isleaf(b);
    //printf("l:");   _print(l);
    _ e = Equality(s, d);
    //printf("e:");   _print(e);
    _ f = AND(e, l);
    //printf("f:");   _print(f);
    B2A_(f, order(v));
    _ tmp = _const(n, 0, order(v));
    _ y = IfThenElse(f, v, tmp);
    _free(c);   _free(s);   _free(d);   _free(l);   _free(e);   _free(f);
    _free(tmp);

    _ z = sum(y);
    _free(y);
    return z;
}

share_t *generate_random_BP(int n)
{
  share_t *BP;
  NEWA(BP, share_t, n*2);

  for (int i=0; i<n*2; i++) {
    BP[i] = i % 2;
  }
  for (int i=0; i<n*2; i++) {
    int p = RANDOM0(n*2);
    share_t tmp = BP[i];
    BP[i] = BP[p];
    BP[p] = tmp;
  }

  int min_depth = 0;
  int min_index = -1;
  int depth = 0;
  for (int i=0; i<n*2; i++) {
    if (BP[i] == 0) {
      depth++;
    } else {
      depth--;
      if (depth < min_depth) {
        min_depth = depth;
        min_index = i;
      }
    }
  }

  share_t *BP2;
  NEWA(BP2, share_t, n*2);

  for (int i=0; i<n*2; i++) {
    int p = (i+min_index+1) % (n*2);
    BP2[i] = BP[p];
  }
  free(BP);

  return BP2;
}



#endif