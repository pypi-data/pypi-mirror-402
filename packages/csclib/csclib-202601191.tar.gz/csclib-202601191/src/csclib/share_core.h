////////////////////////////////////////////
// 構造体の中身をいじったり通信をする関数はこの中に
////////////////////////////////////////////

#ifndef _SHARE_CORE_H
 #define _SHARE_CORE_H

typedef int share_t;
//typedef long share_t;
//typedef packed_array share_t;
typedef share_t pa_t;

///////////////////////////////////////////////////
// 動作を制御するパラメタ
///////////////////////////////////////////////////
struct {
  int parties; // パーティ数（クライアントを含む）
  int channels; // チャンネル数
  int warn_precomp;
  int comm_no_delay;
  int send_queue;
  int oram_check_overflow;
} _opt = {0, 0, 0, 0, 0, 0};

#include "mpc.h"
#include "bits.h"

typedef struct share_array {
  int type; // シェアのタイプ
  int n; // 要素数
  share_t q; // mod
  share_t irr_poly; // 規約多項式
  packed_array A; // 元の値 (party==0) またはシェア (party==1,2)
  int own; // 1 の時は解放しない
}* share_array;
#define _ share_array

#define SHARE_T_RAW 0
#define SHARE_T_22ADD 1
#define SHARE_T_BINARY 2
#define SHARE_T_33ADD 3
#define SHARE_T_SHAMIR 4
#define SHARE_T_RSS 5
#define SHARE_T_ADDITIVE SHARE_T_22ADD


#ifndef MOD
 #define MOD(x) (((x)%(q)+(q)*1) % (q))
#endif

///////////////////////////////////
// 整数の掛け算
// int は 32 bit, long は 64 bit と仮定
// int*int だと桁あふれするので long で計算
///////////////////////////////////
#if 0
share_t LMUL(share_t x, share_t y, share_t q)
{
  long tmp = x;
  tmp = tmp * y;
  tmp = tmp % q;
  tmp = tmp + q;
  tmp = tmp % q;
  if (tmp != MOD(x*y)) {
    printf("LMUL x %d y %d q %d %d %d\n", x, y, q, (int)tmp, MOD(x*y));
  }
  return tmp;
}
#else
 #define LMUL(x, y, q) (((x)*(y))%(q)) // q は 2 のべき乗の場合のみ
#endif


int max_partyid(_ a)
{
  if (a == NULL) {
    printf("max_partyid: a = NULL\n");
    return -1;
  }
  int n = -1;
  switch(a->type) {
  case SHARE_T_22ADD:  n = 2; break;
  case SHARE_T_33ADD:  n = 3; break;
  case SHARE_T_BINARY: n = 2; break;
  case SHARE_T_RSS:    n = 3; break;
  case SHARE_T_SHAMIR: n = 3; break;
  case SHARE_T_RAW:    n = -1; break; // 要検討
  }
  return n;
}


static int len(share_array a)
{
  if (a->type == SHARE_T_RSS) return a->n/2;
  return a->n;
}

static share_t order(share_array a)
{
  return a->q;
}

static packed_array share_raw(share_array a)
{
  return a->A;
}


//#include "beaver.h"

//extern long send_1, send_2, send_3, send_4, send_5, send_6, send_7, send_8;

#ifndef RANDOM0
// #define RANDOM0(n) (rand() % (n))
 //#define RANDOM0(n) (genrand_int32() % (n))
 #define RANDOM0(n) (MT_genrand_int32(mt0) % (n))
#endif


typedef share_array _x;  // xor share (GF(2^d))
typedef share_array _b;  // binary additive (xor) share
typedef share_array _s;  // Shamir's share
typedef share_array _sx;  // Shamir's share (GF(2^d))
typedef share_array _s3; // 3-party additive share
typedef share_array _s3x;  // 3-party additive share (GF(2^d))
typedef share_array _r; // replicated secret share

typedef struct {
  share_array x, y;
} share_pair;
#define _pair share_pair

typedef struct bits {
  int d; // 桁数
  _* a;
}* _bits;

typedef struct {
  _bits x;
  _ y;
} share_pair_bits;
#define _pair_bits share_pair_bits

#ifndef MOD
// #define MOD(x) (((x)+(q)*1) % (q))
 #define MOD(x) (((x)%(q)+(q)*1) % (q))
#endif

/***********************************************************
 * x = f(g(y), z) のときは g(y) のメモリは解放したい
 * z は解放すべきではない．関数の最後で解放する．
 * 関数の返り値は一時的なもので，変数に代入すると確定する
 * 変数への代入は必ず特殊関数を使うことにする
 *   _D(x, f(y))  // x の定義と代入
 *   _M(x, f(y))  // 元の x の解放?と代入
 * 全ての関数で，return 時に一時的な引数の解放を行う
***********************************************************/
//#define _D(x, val) _ x = (val); x->own = 1;
//#define _M(x, val) x = (val); x->own = 1;

static void mpc_send_pa_channel(int party_to, packed_array A, int channel)
{
  if (_party < 0) return;
  void *buf;
  int size;
  packed_array tmp = NULL;

  if (A->type != PA_PACK) {
    tmp = pa_convert(A, PA_PACK);
    buf = tmp->B;
    size = pa_size(tmp);
  } else {
    buf = A->B;
    size = pa_size(A);
  }

//  int c = _num_parties * channel + party_to;
//  mpc_send(c, buf, size);  send_6 += size;
  mpc_send_channel(party_to, buf, size, channel);  //send_6 += size;
  if (tmp) pa_free(tmp);
}
#define mpc_send_pa(party_to, A) mpc_send_pa_channel(party_to, A, 0)


static void mpc_send_share_channel(int party_to, _ A, int channel)
{
  if (_party < 0) return;
//  void *buf = A->A->B;
//  int size = pa_size(A->A);
//  int c = _num_parties * channel + party_to;
//  mpc_send(c, buf, size);  send_6 += size;
//  mpc_send_channel(party_to, buf, size, channel);  //send_6 += size;
  mpc_send_pa_channel(party_to, A->A, channel);  //send_6 += size;
}
#define mpc_send_share(party_to, A) mpc_send_share_channel(party_to, A, 0)

static void mpc_recv_pa_channel(int party_from, packed_array A, int channel)
{
  if (_party < 0) return;
  void *buf;
  int size;
  packed_array tmp = NULL;

  if (A->type != PA_PACK) {
    tmp = pa_new_type(A->n, A->w, PA_PACK);
    buf = tmp->B;
    size = pa_size(tmp);
  } else {
    buf = A->B;
    size = pa_size(A);
  }

//  int c = _num_parties * channel + party_from;
//  mpc_recv(c, buf, size);
  mpc_recv_channel(party_from, buf, size, channel);
  if (tmp) {
    packed_array tmp2 = pa_convert(tmp, A->type);
    free(A->B);
    A->B = tmp2->B;
    free(tmp2);
    pa_free(tmp);
  }
}
#define mpc_recv_pa(party_to, A) mpc_recv_pa_channel(party_to, A, 0)

static void mpc_recv_share_channel(int party_from, _ A, int channel)
{
  if (_party < 0) return;
//  void *buf = A->A->B;
//  int size = pa_size(A->A);
//  int c = _num_parties * channel + party_from;
//  mpc_recv(c, buf, size);
//  mpc_recv_channel(party_from, buf, size, channel);
  mpc_recv_pa_channel(party_from, A->A, channel);
}
#define mpc_recv_share(party_to, A) mpc_recv_share_channel(party_to, A, 0)


static void mpc_exchange_pa_channel(packed_array p_send, packed_array p_recv, int channel)
{
//  if (channel == 0 && _comm_flag > 0) {
//    printf("break\n");
//  }
  void *buf_send, *buf_recv;
  packed_array send_tmp = NULL, recv_tmp = NULL;
  int size;
  if (p_send->type != PA_PACK) {
    send_tmp = pa_convert(p_send, PA_PACK);
    buf_send = send_tmp->B;
    size = pa_size(send_tmp);
  } else {
    buf_send = p_send->B;
    size = pa_size(p_send);
  }
  if (p_recv->type != PA_PACK) {
    recv_tmp = pa_new_type(p_recv->n, p_recv->w, PA_PACK);
    buf_recv = recv_tmp->B;
  } else {
    buf_recv = p_recv->B;
  }

//  mpc_exchange_channel(p_send->B, p_recv->B, pa_size(p_send), channel);
  mpc_exchange_channel(buf_send, buf_recv, size, channel);

  if (p_recv->type != PA_PACK) {
    packed_array tmp2 = pa_convert(recv_tmp, p_recv->type);
    free(p_recv->B);
    p_recv->B = tmp2->B;
    free(tmp2);
    pa_free(recv_tmp);
  }

}


static void mpc_exchange_share_channel(_ share_send, _ share_recv, int channel)
{
  if (_party >  2) return;
  if (_party <= 0) return;

//  void *buf_send = share_send->A->B;
//  void *buf_recv = share_recv->A->B;
//  int size = pa_size(share_send->A);
//  mpc_exchange_channel(buf_send, buf_recv, size, channel);
  mpc_exchange_pa_channel(share_send->A, share_recv->A, channel);
}
#define mpc_exchange_share(send, recv) mpc_exchange_share_channel(send, recv, 0)



//#include "beaver.h"
#include "random.h"



static void share_print(share_array a)
{
//  if (_party >  2) return;
  if (a == NULL) return;
  printf("n = %d q = %d w = %d irr = %d party %d: ", a->n, (int)a->q, a->A->w, a->irr_poly, _party);
  if (a->A != NULL) {
    for (int i=0; i<a->n; i++) printf("%d ", (int)pa_get(a->A, i));
  }
  printf("\n");
}
#define _print share_print

static void share_fprint(FILE *f, share_array a)
{
//  if (_party >  2) return;
  if (a->A == NULL) return;
  fprintf(f, "n = %d q = %d w = %d party %d: ", a->n, (int)a->q, a->A->w, _party);
  for (int i=0; i<a->n; i++) fprintf(f, "%d ", (int)pa_get(a->A, i));
  fprintf(f, "\n");
}


static share_array share_new_channel_type(int n, share_t q, share_t *A, int channel, int pa_type)
{
//  if (pa_type == PA_RAW) {
//    printf("break\n");
//  }
//  if (_party >  2) return NULL;
  int i;
  NEWT(share_array, ans);
//  comm c;
//  comm c1, c2;
  int k;

//  printf("share_new n = %d q = %d\n", n, q);

  ans->type = SHARE_T_ADDITIVE;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  ans->irr_poly = 0;
  k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > 2) return ans;

  ans->A = pa_new_type(n, k, pa_type);
  if (_party <= 0) {
    packed_array A1, A2;
    A1 = pa_new_type(n, k, pa_type);
    A2 = pa_new_type(n, k, pa_type);
    pa_iter itr_ans = pa_iter_new(ans->A);
    pa_iter itr_A1 = pa_iter_new(A1);
    pa_iter itr_A2 = pa_iter_new(A2);
    for (i=0; i<n; i++) {
      share_t r;
      //pa_set(ans->A, i, A[i]);
      pa_iter_set(itr_ans, A[i]);
      //r = RANDOM0(q);
      r = RANDOM(mt_[0][channel], q);
      //pa_set(A1, i, r);
      //pa_set(A2, i, MOD(A[i] - r));
      pa_iter_set(itr_A1, r);
      pa_iter_set(itr_A2, MOD(A[i] - r));
    }
    pa_iter_flush(itr_ans);
    pa_iter_flush(itr_A1);
    pa_iter_flush(itr_A2);
    mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
    mpc_send_pa_channel(TO_PARTY2, A2, channel);

    pa_free(A1);
    pa_free(A2);
  } else {
    mpc_recv_share_channel(FROM_SERVER, ans, channel);
  }

  return ans;
}
#define share_new_channel(n, q, A, channel) share_new_channel_type(n, q, A, channel, PA_PACK)
//#define share_new_channel(n, q, A, channel) share_new_channel_type(n, q, A, channel, PA_RAW)
#define share_new(n, q, A) share_new_channel(n, q, A, 0)
#define share_new_type(n, q, A, pa_type) share_new_channel_type(n, q, A, 0, pa_type)


static share_array share_xor_new_channel(int n, share_t q, share_t *A, int channel)
{
//  if (_party >  2) return NULL;
  int i;
  NEWT(share_array, ans);
//  comm c;
//  comm c1, c2;
  int k;

//  printf("share_new n = %d q = %d\n", n, q);

//  ans->type = -1; // not defined 
//  ans->type = SHARE_T_22XOR;
  ans->type = SHARE_T_ADDITIVE;
  ans->irr_poly = q;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > 2) return ans;

  ans->A = pa_new(n, k);
  if (_party <= 0) {
    packed_array A1, A2;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    for (i=0; i<n; i++) {
      share_t r;
      pa_set(ans->A, i, A[i]);
      r = RANDOM0(q);
      pa_set(A1, i, r);
      pa_set(A2, i, A[i] ^ r);
    }
    mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
    mpc_send_pa_channel(TO_PARTY2, A2, channel);

    pa_free(A1);
    pa_free(A2);
  } else {
    mpc_recv_share_channel(FROM_SERVER, ans, channel);
  }

  return ans;
}
#define share_xor_new(n, q, A) share_xor_new_channel(n, q, A, 0)


#if 1
static share_array share_new_queue_channel(int n, share_t q, share_t *A, int channel)
{
  if (_party >  2) return NULL;
  int i;
  NEWT(share_array, ans);
//  comm c;
//  comm c1, c2;
  int k;

//  printf("share_new n = %d q = %d\n", n, q);

  ans->type = SHARE_T_ADDITIVE;
  ans->n = n;
  ans->q = q;
  ans->own = 0;
  k = blog(q-1)+1;

  ans->A = NULL;
  if (_party > 2) return ans;


  ans->A = pa_new(n, k);
  if (_party <= 0) {
    packed_array A1, A2;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    for (i=0; i<n; i++) {
      share_t r;
      pa_set(ans->A, i, A[i]);
      r = RANDOM0(q);
      pa_set(A1, i, r);
      pa_set(A2, i, MOD(A[i] - r));
    }
    //mpc_send_queue_channel(TO_PARTY1, A1->B, pa_size(A1), channel);  send_7 += pa_size(A1);
    //mpc_send_queue_channel(TO_PARTY2, A2->B, pa_size(A2), channel);
    mpc_send_pa_channel(TO_PARTY1, A1, channel);  //send_7 += pa_size(A1);
    mpc_send_pa_channel(TO_PARTY2, A2, channel);

    pa_free(A1);
    pa_free(A2);
  } else {
    //mpc_recv_share_channel(FROM_SERVER, ans, channel);
    mpc_recv_pa_channel(FROM_SERVER, ans->A, channel);
  }

  return ans;
}
#endif

static void share_free(share_array a)
{
//  if (_party >  2) return;
  if (a == NULL) return;
  if (a->A != NULL) pa_free(a->A);
  free(a);
}
#define _free share_free

static void share_save(share_array a, char *filename)
{
  if (_party >  2) return; // 要検討
  char buf[100];
  int p = _party;
  if (p < 0) p = 0;
  sprintf(buf, "%s%d.txt", filename, p);
  FILE *f = fopen(buf, "w");
  if (f == NULL) {
    perror("share_save: ");
  }
  int n = len(a);
  fprintf(f, "%d %d\n", n, (int)order(a));
  for (int i=0; i<n; i++) {
  //  fprintf(f, "%d\n", (int)a->A[i]);
    fprintf(f, "%d\n", (int)pa_get(a->A, i));
  }
  fclose(f);
}
#define _save share_save

static share_array share_load(char *filename)
{
  if (_party >  2) return NULL; // 要検討
  char buf[100];
  int p = _party;
  if (p < 0) p = 0;
  sprintf(buf, "%s%d.txt", filename, p);
  FILE *f = fopen(buf, "r");
  if (f == NULL) {
    perror("share_load: ");
  }
  int n;
  share_t q, v;
  int qtmp;
  fscanf(f, " %d %d", &n, &qtmp);
  q = qtmp;
  int k = blog(q-1)+1;
  NEWT(share_array, a);
  a->A = pa_new(n, k);
  a->n = n;
  a->q = q;
  for (int i=0; i<n; i++) {
    int vtmp;
    fscanf(f, " %d", &vtmp);
    v = vtmp;
    pa_set(a->A, i, v);
  }
  fclose(f);
  return a;
}
#define _load share_load

#include "precompute.h"

static void share_save_binary(share_array a, FILE *f)
{
  //if (_party >  2) return; // 要検討
  writeuint(1,ID_SHARE,f);
  writeuint(sizeof(a->type), a->type, f);
  writeuint(sizeof(a->n), a->n, f);
  writeuint(sizeof(a->q), a->q, f);
  writeuint(sizeof(a->irr_poly), a->irr_poly, f);

  pa_write(a->A, f);

}
#define _save_binary share_save_binary

static void share_save_binary_to_file(share_array a, char *filename)
{
  if (_party >  max_partyid(a)) return;

  int p = _party;
  if (p < 0) p = 0;
  char *fname = precomp_fname(filename, p);

  FILE *f = fopen(fname, "w");
  if (f == NULL) {
    perror("share_save_binary_to_file: ");
  }
  share_save_binary(a, f);

  fclose(f);
  free(fname);
}

static _ share_load_binary(uchar **p_)
{
  uchar *p = *p_;

  int type = getuint(p,0,1);  p += 1;
  if (type != ID_SHARE) {
    printf("share_load_binary: ID = %d\n", type);
    exit(1);
  }

  NEWT(_, ans);
  ans->type = getuint(p,0,sizeof(ans->type));  p += sizeof(ans->type);
  ans->n = getuint(p,0,sizeof(ans->n));  p += sizeof(ans->n);
  ans->q = getuint(p,0,sizeof(ans->q));  p += sizeof(ans->q);
  ans->irr_poly = getuint(p,0,sizeof(ans->irr_poly));  p += sizeof(ans->irr_poly);
  ans->own = 0;
  ans->A = pa_read(&p);

  *p_ = p;
  return ans;
}
#define _load_binary share_load_binary

static _ share_load_binary_from_file(char *filename)
{
  if (_party >  2) return NULL; // 要検討
  //if (_party >  max_partyid(a)) return;

  int party = _party;
  if (party < 0) party = 0;
  char *fname = precomp_fname(filename, party);

  MMAP *map = NULL;
  map = mymmap(fname);
  uchar *p = (uchar *)map->addr;

  _ ans = share_load_binary(&p);

  free(fname);

  return ans;
}

static void share_check(share_array a)
{
  if (_party >  2) return; // 要検討
  if (a->type != SHARE_T_22ADD) {
    printf("share_check: type = %d\n", a->type);
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
    packed_array A1, A2;
    A1 = pa_new(n, k);
    A2 = pa_new(n, k);
    printf("check party %d: ", _party);
    mpc_recv_pa(FROM_PARTY1, A1);
    mpc_recv_pa(FROM_PARTY2, A2);
    if (_party == 0) {
      for (i=0; i<n; i++) {
        share_t x;
        x = MOD(q + pa_get(A1, i) + pa_get(A2, i));
        if ((u64)x != pa_get(a->A, i)) {
          printf("i = %d A = %d %d A1 = %d A2 = %d\n", i, (int)pa_get(a->A, i), (int)x, (int)pa_get(A1,i), (int)pa_get(A2,i));
          err=1;
          exit(1);
        }
      }
      printf("check done\n");
    }
    pa_free(A1);
    pa_free(A2);
  } else {
    printf("check party %d: \n", _party);
    mpc_send_share(TO_SERVER, a);
  }
}
#define _check share_check

static share_array share_reconstruct_channel(share_array a, int channel)
{
  if (_party >  2) return NULL;

  if (a->type != SHARE_T_22ADD) {
    printf("share_reconstruct: type = %d\n", a->type);
  }

  int i, n;
//  comm c;
  share_t q;

  int mode = 0;

  NEWT(share_array, ans);
  *ans = *a;
  n = a->n;
  q = a->q;
  int k = blog(q-1)+1;
  ans->type = a->type;
  ans->A = pa_new_type(n, k, a->A->type);

  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_a = pa_iter_new(a->A);
  //pa_iter_new(a->A);
  if (_party <= 0) {
    for (i=0; i<n; i++) {
      //pa_set(ans->A, i, pa_get(a->A, i));
      pa_iter_set(itr_ans, pa_iter_get(itr_a));
    }
  } else {
    packed_array x;
//    share_t *tmp;
    x = pa_new_type(n, k, a->A->type);
    if (mode == 0) {
      mpc_exchange_channel(a->A->B, x->B, pa_size(a->A), channel);
      pa_iter itr_x = pa_iter_new(x);
      for (i=0; i<n; i++) {
        //pa_set(ans->A, i, MOD(pa_get(a->A,i) + pa_get(x,i)));
        pa_iter_set(itr_ans, MOD(pa_iter_get(itr_a)+ pa_iter_get(itr_x)));
      }
      pa_iter_free(itr_x);
    } else {
#if 0
      if (_party != mode) { // 要確認
        mpc_send_share_channel(TO_PAIR, a, channel);  //send_8 += pa_size(a->A);
      } else {
        //pa_iter itr_x = pa_iter_new(x);
        mpc_recv_pa_channel(FROM_PAIR, x, channel);
        for (i=0; i<n; i++) {
          pa_set(ans->A, i, MOD(pa_get(a->A,i) + pa_get(x,i)));
        }
        //pa_iter_free(itr_x);
      }
#endif
    }
    pa_free(x);
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a);
  return ans;
}
//#define share_reconstruct_channel(a, channel) share_reconstruct_channel_type(a, channel, PA_PACK)
#define _reconstruct_channel share_reconstruct_channel
#define share_reconstruct(a) share_reconstruct_channel(a, 0)
#define _reconstruct share_reconstruct


static share_array share_reconstruct_xor_channel(share_array a, int channel)
{
  if (_party >  2) return NULL;

  if (a->type != SHARE_T_ADDITIVE || a->irr_poly == 0) {
    //printf("share_reconstruct_xor: type = %d irr_poly = %x\n", a->type, a->irr_poly);
  }

  int i, n;
//  comm c;
  share_t q;

//  printf("share_reconstruct\n");
  NEWT(share_array, ans);
  *ans = *a;
  n = a->n;
  q = a->q;
  int k = blog(q-1)+1;
  ans->A = pa_new(n, k);

  if (_party <= 0) {
    for (i=0; i<n; i++) {
      pa_set(ans->A, i, pa_get(a->A, i));
    }
  } else {
    packed_array x;
    x = pa_new(n, k);
    mpc_exchange_channel(a->A->B, x->B, pa_size(a->A), channel);
    for (i=0; i<n; i++) {
      pa_set(ans->A, i, pa_get(a->A,i) ^ pa_get(x,i));
    }
    pa_free(x);
  }
  return ans;
}
#define share_reconstruct_xor(a) share_reconstruct_xor_channel(a, 0)
#define _reconstruct_xor share_reconstruct_xor

share_t* return_secret(share_array x) {
    packed_array a1, a2;
    share_t *ans = NULL;
    if (_party == 0) {
        a1 = pa_new(x->n, x->A->w);
        a2 = pa_new(x->n, x->A->w);
        mpc_recv(1, a1->B, pa_size(a1));
        mpc_recv(2, a2->B, pa_size(a2));
        NEWA(ans, share_t, x->n);
        for (int i = 0; i < x->n; ++i) {
            ans[i] = (pa_get(a1, i) + pa_get(a2, i)) % x->q;
        }
        pa_free(a1);
        pa_free(a2);
    }
    else if (_party >= 1 && _party <= 2) {
        mpc_send(0, x->A->B, pa_size(x->A));
    }
    return ans;
}



static void _print_debug(_ a)
{
  _ tmp = _reconstruct(a);
  printf("debug "); _print(tmp);
  _free(tmp);
}
static void _print_debug_xor(_ a)
{
  _ tmp = _reconstruct_xor(a);
  printf("debug "); _print(tmp);
  _free(tmp);
}
static void _print_debug_channel(_ a, int channel)
{
  _ tmp = _reconstruct_channel(a, channel);
  printf("debug "); _print(tmp);
  _free(tmp);
}
static void _print_debug_bits(_bits a)
{
  for (int i=0; i<a->d; i++) {
    _ tmp = _reconstruct(a->a[i]);
    printf("debug "); _print(tmp);
    _free(tmp);
  }
}


///////////////////////////////////////////////////
// a に乱数 r, -r を加える
// 乱数列を共有することにも使える（これを別に作る方が良い？）
///////////////////////////////////////////////////
static void share_randomize(share_array a)
{
  if (_party >  2) return;
  if (_party <= 0) return;

  if (a->type != SHARE_T_22ADD) {
    printf("share_randomize: type = %d\n", a->type);
  }

#if 0
  unsigned long init[5]={0x123, 0x234, 0x345, 0x456, 0};

  if (_party == 1) { // TODO: 共有乱数を使うように変更
    init[4] = 1; // rand();
    mpc_send(TO_PARTY2, init, sizeof(init[0])*5);
  } else {
    mpc_recv(FROM_PARTY1, init, sizeof(init[0])*5);
  }
//  init_by_array(init, 5);
  MT m0 = MT_init_by_array(init, 5);
#endif

  share_t q, x, r;
  q = order(a);
  int n = len(a);
  for (int i=0; i<n; i++) {
    //r = RANDOM(m0, q);
    r = RANDOM0(q);
    x = pa_get(a->A, i);
    if (_party == 1) {
      x = MOD(x + r);
    } else {
      x = MOD(x - r);
    }
    pa_set(a->A, i, x);
  }
  //MT_free(m0);
}
#define _randomize share_randomize


static share_array share_dup(share_array a)
{
//  if (_party >  2) return NULL;
//  printf("dup "); _print(a);
  if (a == NULL) {
    printf("share_dup: a == NULL\n");
    return NULL;
  }
  NEWT(share_array, D);
  *D = *a;
  D->A = NULL;
  if (a->A != NULL) {
    //D->A = pa_dup(a->A);
    //D->A = pa_new(D->n, a->A->w); // pa_new 内でメモリを初期化していないと valgrind でエラーが出る
    D->A = pa_new_type(D->n, a->A->w, a->A->type); // pa_new 内でメモリを初期化していないと valgrind でエラーが出る
    //for (int i=0; i<D->n; i++) pa_set(D->A,i, pa_get(a->A,i));
    memcpy(D->A->B, a->A->B, pa_size(a->A));
  }
  return D;
}
#define _dup share_dup



//////////////////////////////////
// P0, P1, P2 で同期をとる
//////////////////////////////////
void _sync(void)
{
  if (_party >  2) return;
  share_t A[1] = {0};
  _ tmp = share_new(1, 2, A);
//  _ tmp2 = _reconstruct(tmp);
  _check(tmp);
  _free(tmp);
//  _free(tmp2);
//  printf("sync\n");
//  getchar();
}

void _sync_channel(int channel)
{
  if (_party >  2) return;
  char tmp[1];
  tmp[0] = '$';
  if (_party == 0) {
    mpc_send_channel(TO_PARTY1, tmp, 1, channel);
    mpc_send_channel(TO_PARTY2, tmp, 1, channel);
    mpc_recv_channel(FROM_PARTY1, tmp, 1, channel);
    mpc_recv_channel(FROM_PARTY2, tmp, 1, channel);
  }
  tmp[0] = '?';
  if (_party == 1 || _party == 2) {
    mpc_recv_channel(FROM_SERVER, tmp, 1, channel);
    //printf("sync: recv %c %d\n", tmp[0], tmp[0]);
    if (tmp[0] != '$') {
      printf("!sync: recv %c %d\n", tmp[0], tmp[0]);
      exit(1);
    }
    mpc_send_channel(TO_SERVER, tmp, 1, channel);
  }
}

void _sync3_channel(int channel)
{
  if (_party >  3) return;
  char tmp[1];
  tmp[0] = '$';
  if (_party == 0) {
    mpc_send_channel(TO_PARTY1, tmp, 1, channel);
    mpc_send_channel(TO_PARTY2, tmp, 1, channel);
    mpc_send_channel(TO_PARTY3, tmp, 1, channel);
    mpc_recv_channel(FROM_PARTY1, tmp, 1, channel);
    mpc_recv_channel(FROM_PARTY2, tmp, 1, channel);
    mpc_recv_channel(FROM_PARTY3, tmp, 1, channel);
  }
  tmp[0] = '?';
  if (_party == 1 || _party == 2 || _party == 3) {
    mpc_recv_channel(FROM_SERVER, tmp, 1, channel);
    if (tmp[0] != '$') {
      printf("sync3: recv %c %d\n", tmp[0], tmp[0]);
      exit(1);
    }
    mpc_send_channel(TO_SERVER, tmp, 1, channel);
  }
}
#define _sync3() _sync3_channel(0)


//////////////////////////////////
// a := b (古い a, b のメモリを解放する)
//////////////////////////////////
static void share_move_(share_array a, share_array b)
{
//  if (_party >  2) return;
  if (a == NULL || b == NULL) {
    printf("move_ a = %p b = %p\n", a, b);
    return;
  }
  if (a->A != NULL) pa_free(a->A);
  *a = *b;
  free(b);
}
#define _move_ share_move_

static share_array share_move(share_array b)
{
  //if (_party >  2) return NULL;
  if (b == NULL) {
    printf("move b = %p\n", b);
  }
  return b;
}
#define _move share_move

///////////////////////////////////////
// シェアの片割れを得る
///////////////////////////////////////
static share_t share_getraw(share_array a, int i)
{
  if (a == NULL) {
    printf("share_getraw: a = NULL\n");
    return 0;
  }
  //if (a->A == NULL) return 0;
  if (a->A == NULL) {
    printf("share_getraw: a->A = NULL\n");
    return 0;
  }
  if (i < 0 || i >= a->n) {
    printf("share_getraw: n %d i %d\n", a->n, i);
  }
  return pa_get(a->A,i);
}

static void share_setraw(share_array a, int i, share_t x)
{
  if (a == NULL) {
    printf("share_setraw: a = NULL\n");
    return;
  }
  //if (a->A == NULL) return 0;
  if (a->A == NULL) {
    printf("share_setraw: a->A = NULL\n");
    return;
  }
  if (i < 0 || i >= a->n) {
    printf("share_setraw: n %d i %d\n", a->n, i);
  }
  if (x < 0) {
    printf("share_setraw: x %d q %d\n", x, a->q);
  }
  if (a->A == NULL) return;
  share_t q = a->q;
  pa_set(a->A, i, MOD(x));
}

#if 0
static void share_iter_setraw(share_array a, share_t x)
{
  if (a->A == NULL) {
    printf("share_setraw: a->A = NULL\n");
    return;
  }
  share_t q = a->q;
  pa_iter_set(a->A, MOD(x));
}

static void share_iter_setraw_flush(share_array a)
{
  pa_iter_flush(a->A);
}
#endif

_ share_const_rss_GF(int n, share_t v, share_t q, share_t irr_poly);

static share_array share_const_type2(int n, share_t v, share_t q, int type, int pa_type)
{
//  if (_party >  2) return NULL;
//  if (type == SHARE_T_RSS) {
//    return share_const_rss_GF(n, v, q, 0);
//  }
  NEWT(share_array, ans);
  int n2 = n;
  if (type == SHARE_T_RSS) n2 = n*2;
  ans->n = n2;
  ans->q = q;
  ans->irr_poly = 0;
  ans->type = type;
  int k = blog(q-1)+1;
  ans->A = NULL;
  if (_party > max_partyid(ans)) return ans;
  ans->A = pa_new_type(n2, k, pa_type); // TODO: これだと 3 party で 22ADD でも party 3 でメモリを確保する
#if 0
  for (int i=0; i<n; i++) {
    if (_party >= 2) {
      pa_set(ans->A, i, 0);
    } else {
      pa_set(ans->A, i, v);
    }
  }
#else
  if (_party >= 2) {
    memset(ans->A->B, 0, pa_size(ans->A));
  } else {
    if (v == 0) {
      memset(ans->A->B, 0, pa_size(ans->A));
    } else {
      pa_iter itr_ans = pa_iter_new(ans->A);
      for (int i=0; i<n; i++) {
        pa_iter_set(itr_ans, v);
      }
      pa_iter_flush(itr_ans);
    }
  }
#endif
  return ans;
}
#define share_const_type(n, v, q, type) share_const_type2(n, v, q, type, PA_PACK)
#define share_const(n, v, q) share_const_type(n, v, q, SHARE_T_22ADD)
#define _const share_const
#define _const_shamir(n, v, q) share_const_type(n, v, q, SHARE_T_SHAMIR)


///////////////////////////////////////
// x は公開の平文
///////////////////////////////////////
static void share_setpublic(share_array a, int i, share_t x)
{
//  if (_party >  2) return;
  //if (_party >  3) return;
  if (a == NULL) {
    printf("share_setpublic: a = NULL\n");
    return;
  }
  if (_party > max_partyid(a)) return;
  if (i < 0 || i >= a->n) {
    printf("share_setpublic n %d i %d\n", a->n, i);
  }
  share_t q = a->q;
  if (_party >= 2) {
    if (a->A != NULL) pa_set(a->A, i, 0);
  } else {
    pa_set(a->A, i, MOD(x));
  }
}
#define _setpublic share_setpublic

#if 0
static void share_iter_setpublic(share_array a, share_t x)
{
  if (a == NULL) {
    printf("share_iter_setpublic: a = NULL\n");
    return;
  }
  if (_party > max_partyid(a)) return;
  share_t q = a->q;
  if (_party >= 2) {
    x = 0;
  } else {
    x = MOD(x);
  }
  pa_iter_set(a->A, x);
}

static void share_iter_setpublic_flush(share_array a)
{
  if (a == NULL) {
    printf("share_iter_setpublic: a = NULL\n");
    return;
  }
  if (_party > max_partyid(a)) return;
  pa_iter_flush(a->A);
}
#endif


////////////////////////////////////////////
// a[i] := b[j]
////////////////////////////////////////////
static void share_setshare(share_array a, int i, share_array b, int j)
{
  //if (_party >  2) return;
  if (a == NULL || b == NULL) {
    printf("share_setshare: a = %p b = %p\n", a, b);
    return;
  }
  if (_party > max_partyid(a)) return;

  if (i < 0 || i >= a->n) {
    printf("share_setshare a: n %d i %d\n", a->n, i);
    exit(1);
  }
  if (j < 0 || j >= b->n) {
    printf("share_setshare b: n %d j %d\n", b->n, j);
    exit(1);
  }
  if (a->q != b->q) {
    printf("share_setshare a->q %d b->q %d\n", (int)a->q, (int)b->q);
    exit(1);
  }
  if (a->A != NULL && b->A != NULL) pa_set(a->A,i, pa_get(b->A,j));
}
#define _setshare share_setshare

////////////////////////////////////////////
// a[is:ie) := b[js:je)
////////////////////////////////////////////
static void share_setshares(share_array a, int is, int ie, share_array b, int js)
{
//  if (_party >  2) return;
  if (a == NULL || b == NULL) {
    printf("share_setshares: a = %p b = %p\n", a, b);
    return;
  }
  if (_party > max_partyid(a)) return;

  if (is < 0 || is >= a->n) {
    printf("share_setshares a: n %d is %d\n", a->n, is);
    exit(1);
  }
  if (ie > a->n) {
    printf("share_setshares a: n %d ie %d\n", a->n, ie);
    exit(1);
  }
  if (js < 0 || js >= b->n) {
    printf("share_setshares b: n %d js %d\n", b->n, js);
    exit(1);
  }
  if (js + (ie-is) > b->n) {
    printf("share_setshares b: n %d is %d ie %d js %d\n", b->n, is, ie, js);
    exit(1);
  }
  if (a->q != b->q) {
    printf("share_setshares a->q %d b->q %d\n", (int)a->q, (int)b->q);
    exit(1);
  }
  //pa_iter itr_a = pa_iter_new(a->A);
  pa_iter itr_b = pa_iter_pos_new(b->A, js);
  if (a->A != NULL && b->A != NULL) {
    for (int i = 0; i < ie-is; i++) {
      //pa_set(a->A,is + i, pa_get(b->A,js + i));
      //pa_iter_set(itr_a, pa_iter_get(itr_b));
      pa_set(a->A,is + i, pa_iter_get(itr_b));
    }
  }
  //pa_iter_flush(itr_a); 
  pa_iter_free(itr_b);
}
#define _setshares share_setshares


static void share_addpublic(share_array a, int i, share_t x)
{
  //if (_party >  2) return;
  if (a == NULL) {
    printf("share_addpublic: a = %p\n", a);
    return;
  }
  if (_party > max_partyid(a)) return;
  if (i < 0 || i >= a->n) {
    printf("share_addpublic n %d i %d\n", a->n, i);
  }
  share_t q = a->q;
  if (_party != 2) pa_set(a->A, i, MOD(pa_get(a->A,i) + x));
}
#define _addpublic share_addpublic

static void share_subpublic(share_array a, int i, share_t x)
{
  //if (_party >  2) return;
  if (a == NULL) {
    printf("share_subpublic: a = %p\n", a);
    return;
  }
  if (_party > max_partyid(a)) return;
  if (i < 0 || i >= a->n) {
    printf("share_subpublic n %d i %d\n", a->n, i);
  }
  share_t q = a->q;
  if (_party != 2) pa_set(a->A, i, MOD(pa_get(a->A,i) + q - x));
}
#define _subpublic share_subpublic

static void share_addshare_shamir(share_array a, int i, share_array b, int j)
{
//  if (_party >  2) return;
  if (a == NULL || b == NULL) {
    printf("share_addshare_shamir: a = %p b = %p\n", a, b);
    return;
  }
  if (_party > max_partyid(a)) return;
  if (i < 0 || i >= a->n) {
    printf("share_addshare a: n %d i %d\n", a->n, i);
  }
  if (j < 0 || j >= b->n) {
    printf("share_addshare b: n %d j %d\n", b->n, j);
  }
  if (a->q != b->q) {
    printf("share_addshare a->q %d b->q %d\n", (int)a->q, (int)b->q);
  }
  share_t q = a->q;
  pa_set(a->A,i,MOD(pa_get(a->A,i) + pa_get(b->A,j)));
}
#define _addshare_shamir share_addshare_shamir

static void share_addshare(share_array a, int i, share_array b, int j)
{
  if (a == NULL || b == NULL) {
    printf("share_addshare: a = %p b = %p\n", a, b);
    return;
  }
  if (_party > max_partyid(a)) return;
  //if (_party >  2) return;
  share_addshare_shamir(a, i, b, j);
}
#define _addshare share_addshare


static void share_subshare(share_array a, int i, share_array b, int j)
{
  if (a == NULL || b == NULL) {
    printf("share_subshare: a = %p b = %p\n", a, b);
    return;
  }
  if (_party > max_partyid(a)) return;
  //if (_party >  2) return;
  if (i < 0 || i >= a->n) {
    printf("share_subshare a: n %d i %d\n", a->n, i);
  }
  if (j < 0 || j >= b->n) {
    printf("share_subshare b: n %d j %d\n", b->n, j);
  }
  if (a->q != b->q) {
    printf("share_subshare a->q %d b->q %d\n", (int)a->q, (int)b->q);
  }
  share_t q = a->q;
  pa_set(a->A,i,MOD(pa_get(a->A,i) + q - pa_get(b->A,j)));
}
#define _subshare share_subshare


static void share_mulpublic(share_array a, int i, int x)
{
  if (a == NULL) {
    printf("share_mulpublic: a = %p\n", a);
    return;
  }
  if (_party > max_partyid(a)) return;
  //if (_party >  2) return;
  if (i < 0 || i >= a->n) {
    printf("share_mulpublic n %d i %d\n", a->n, i);
  }
  share_t q = a->q;
  pa_set(a->A, i, LMUL(pa_get(a->A,i), x, q));
}
#define _mulpublic share_mulpublic

/////////////////////////////////////////
// [start, end-1] の範囲を切り出す
// end は含まないことに注意（Python風）
/////////////////////////////////////////
static share_array share_slice_raw(share_array a, int start, int end)
{
  if (a == NULL) {
    printf("share_slice_raw: a = %p\n", a);
    return NULL;
  }
//  if (_party >  2) return NULL;
  if (start < 0) start = a->n + start;
  if (end <= 0) end = a->n + end;
  if (start < 0 || start > a->n) {
    printf("share_slice n %d start %d\n", a->n, start);
  }
  if (end < 0 || end > a->n) {
    printf("share_slice n %d end %d\n", a->n, end);
  }
  //  printf("share_slice n %d start %d\n", a->n, start);
  //  printf("share_slice n %d end %d\n", a->n, end);
  NEWT(share_array, ans);
  *ans = *a;
  ans->n = end - start;
  ans->q = a->q;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(ans->n, a->A->w, a->A->type);
#if 0
  for (int i=0; i<ans->n; i++) pa_set(ans->A,i,pa_get(a->A,start+i));
#else
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr = pa_iter_pos_new(a->A, start);
  for (int i=0; i<ans->n; i++) pa_iter_set(itr_ans, pa_iter_get(itr));
  pa_iter_flush(itr_ans);
  pa_iter_free(itr);


//  printf("slice ans "); _print_debug(ans);
//  _ tmp = _dup(ans);
//  for (int i=0; i<tmp->n; i++) pa_set(tmp->A,i,pa_get(a->A,start+i));
//  printf("slice tmp "); _print_debug(tmp);

#endif
  return ans;
}
#define _slice_raw share_slice_raw
#define share_slice share_slice_raw
#define _slice share_slice_raw

static void share_slice_(share_array a, int start, int end)
{
  if (a == NULL) {
    printf("share_slice_: a = %p\n", a);
    return;
  }
//  if (_party >  2) return;
  share_array tmp = share_slice(a, start, end);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _slice_ share_slice_

static share_t debug_get(share_array a, int i)
{
  _ tmp = share_slice(a, i, i+1);
  _ tmp2 = _reconstruct(tmp);
  share_t ans = share_getraw(tmp2, 0);
  _free(tmp); _free(tmp2);
  return ans;
}


static share_array share_concat(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("share_concat: a = %p b = %p\n", a, b);
    return NULL;
  }
  //if (_party >  2) return NULL;
  if (a->q != b->q) {
    printf("share_concat a->q %d b->q %d\n", (int)a->q, (int)b->q);
  }
  NEWT(share_array, ans);
  ans->n = a->n + b->n;
  ans->q = a->q;
  ans->type = a->type;
  ans->irr_poly = a->irr_poly;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(ans->n, a->A->w, a->A->type);
  for (int i=0; i<a->n; i++) pa_set(ans->A,i,pa_get(a->A,i)); // 要高速化
  for (int i=0; i<b->n; i++) pa_set(ans->A,a->n + i, pa_get(b->A,i));
  return ans;
}
#define _concat share_concat

static void share_concat_(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("share_concat_: a = %p b = %p\n", a, b);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = share_concat(a, b);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _concat_ share_concat_



static share_array share_insert_head(share_array a, share_t x)
{
  if (a == NULL) {
    printf("share_insert_head: a = %p\n", a);
    return NULL;
  }
  //if (_party >  2) return NULL;
  NEWT(share_array, ans);
  ans->n = a->n + 1;
  ans->q = a->q;
  ans->type = a->type;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(ans->n, a->A->w, a->A->type);
  if (_party < 2) {
    pa_set(ans->A, 0, x);
  } else {
    pa_set(ans->A, 0, 0);
  }
  for (int i=1; i<ans->n; i++) pa_set(ans->A, i, pa_get(a->A, i-1));
  return ans;
}
#define _insert_head share_insert_head

static void share_insert_head_(share_array a, share_t x)
{
  if (a == NULL) {
    printf("share_insert_head_: a = %p\n", a);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = share_insert_head(a, x);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _insert_head_ share_insert_head_

static share_array share_insert_tail(share_array a, share_t x)
{
  if (a == NULL) {
    printf("share_insert_tail: a = %p\n", a);
    return NULL;
  }
  //if (_party >  2) return NULL;
  NEWT(share_array, ans);
  *ans = *a;
  ans->n = a->n + 1;
  ans->q = a->q;
  //if (ans->A == NULL) return ans;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(ans->n, a->A->w, a->A->type);
  if (_party < 2) {
    pa_set(ans->A, ans->n-1, x);
  } else {
    pa_set(ans->A, ans->n-1, 0);
  }
  for (int i=0; i<ans->n-1; i++) pa_set(ans->A, i, pa_get(a->A, i));
  return ans;
}
#define _insert_tail share_insert_tail

static void share_insert_tail_(share_array a, share_t x)
{
  if (a == NULL) {
    printf("share_insert_tail_: a = %p\n", a);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = share_insert_tail(a, x);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _insert_tail_ share_insert_tail_

////////////////////////////////////////////////////////////////////
// GF/additive, 22ADD, 33ADD, RSS どれでも動作する（はず）
////////////////////////////////////////////////////////////////////
static share_array vadd(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("vadd: a = %p b = %p\n", a, b);
    return NULL;
  }
//  if (_party >  2) return NULL;
  //if (_party >= 3 && a->type != SHARE_T_SHAMIR) return NULL; // 要check
  int n = a->n;
  share_t q = a->q;
  if (a->n != b->n) {
    printf("vadd a->n = %d b->n = %d\n", a->n, b->n);
  }
  if (a->q != b->q) {
    printf("vadd a->q = %d b->q = %d\n", (int)a->q, (int)b->q);
  }
  if (a->irr_poly != b->irr_poly) {
    printf("vadd: a->irrpoly = %x b->irrpoly = %x\n", a->irr_poly, b->irr_poly);
  }
  NEWT(share_array, ans);
  *ans = *a;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  //if (_party > 2) {
  //  ans->A = NULL;
  //  return ans;
  //}
  ans->A = pa_new_type(a->n, a->A->w, a->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_a = pa_iter_new(a->A);
  pa_iter itr_b = pa_iter_new(b->A);
  for (int i=0; i<n; i++) {
    //pa_set(ans->A, i, MOD(pa_get(a->A, i) + pa_get(b->A, i)));
    //pa_iter_set(itr_ans, MOD(pa_iter_get(itr_a) + pa_iter_get(itr_b)));
    share_t za = pa_iter_get(itr_a);
    share_t zb = pa_iter_get(itr_b);
    share_t zc;
    if (ans->irr_poly) {
      zc = za ^ zb;
    } else {
      zc = MOD(za + zb);
    }
    //printf("za %d zb %d zc %d\n", za, zb, zc);
    pa_iter_set(itr_ans, zc);
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a); pa_iter_free(itr_b);
  return ans;
}
#define _vadd vadd

static void vadd_(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("vadd_: a = %p b = %p\n", a, b);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = vadd(a, b);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _vadd_ vadd_

static share_array vsub(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("vsub: a = %p b = %p\n", a, b);
    return NULL;
  }
  //if (_party >  2) return NULL;
  int n = a->n;
  share_t q = a->q;
  if (a->n != b->n) {
    printf("vsub a->n = %d b->n = %d\n", a->n, b->n);
  }
  if (a->q != b->q) {
    printf("vsub a->q = %d b->q = %d\n", (int)a->q, (int)b->q);
  }
  if (a->irr_poly != b->irr_poly) {
    printf("vsub: a->irrpoly = %d b->irrpoly = %d\n", a->irr_poly, b->irr_poly);
  }
  NEWT(share_array, ans);
  *ans = *a;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(a->n, a->A->w, a->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_a = pa_iter_new(a->A);
  pa_iter itr_b = pa_iter_new(b->A);
  for (int i=0; i<n; i++) {
    // pa_set(ans->A, i, MOD(pa_get(a->A, i) - pa_get(b->A, i))); // ここがバグってる pa_getは符号なし整数なので，pa_get(a->A, i) < pa_get(b->A, i)の時，値が壊れる．
    //pa_set(ans->A, i, (pa_get(a->A, i) + q - pa_get(b->A, i)) % q);
    share_t za = pa_iter_get(itr_a);
    share_t zb = pa_iter_get(itr_b);
    share_t zc;
    if (ans->irr_poly) {
      zc = za ^ zb;
    } else {
      zc = MOD(za + q - zb);
    }
    pa_iter_set(itr_ans, zc);
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a); pa_iter_free(itr_b);
  return ans;
}
#define _vsub vsub

static void vsub_(share_array a, share_array b)
{
  if (a == NULL || b == NULL) {
    printf("vsub_: a = %p b = %p\n", a, b);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = vsub(a, b);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _vsub_ vsub_

#include "beaver.h"

static share_array vmul_channel(share_array x, share_array y, int channel)
{
  if (x == NULL || y == NULL) {
    printf("vmul: x = %p y = %p\n", x, y);
    return NULL;
  }
  if (_party > 0 && (x->type != SHARE_T_22ADD || y->type != SHARE_T_22ADD)) {
    printf("vmul: x->type = %d y->type = %d\n", x->type, y->type);
    return NULL;
  }
  if (_party >  2) {
    NEWT(_, ans);
    *ans = *x;
    ans->A = NULL;
    return ans;
  }
  int n = x->n;
  share_t q = x->q;
  int i;
  if (x->n != y->n) {
    printf("vmul x->n = %d y->n = %d\n", x->n, y->n);
  }
  if (x->q != y->q) {
    printf("vmul x->q = %d y->q = %d\n", (int)x->q, (int)y->q);
  }
  NEWT(share_array, ans);
  *ans = *x;
  ans->A = NULL;
  //if (_party > max_partyid(x)) return ans;
  ans->A = pa_new_type(n, x->A->w, x->A->type);

// Beaver Triple の計算
  BeaverTriple bt;
//  printf("channel %d tbl %p\n", channel, BT_tbl[channel]);

  if (BT_tbl[channel] != NULL) {
  //  printf("using bt tbl\n");
    bt = BeaverTriple_new3(n, q, BT_tbl[channel]); // 事前計算
  } else {
    if (_opt.warn_precomp) printf("without bt tbl\n");
    //bt = BeaverTriple_new_channel(n, q, x->A->w, channel);
    if (_party >= 0) bt = BeaverTriple_new_channel(n, q, x->A->w, channel);
  }
  if (_party <= 0) {
    pa_iter itr_ans = pa_iter_new(ans->A);
    pa_iter itr_x = pa_iter_new(x->A);
    pa_iter itr_y = pa_iter_new(y->A);
    for (i=0; i<n; i++) {
      //pa_set(ans->A, i, LMUL(pa_get(x->A,i), pa_get(y->A,i), q));
      pa_iter_set(itr_ans, LMUL(pa_iter_get(itr_x), pa_iter_get(itr_y), q));
    }
    pa_iter_flush(itr_ans); pa_iter_free(itr_x); pa_iter_free(itr_y);
    if (_party == -1) return ans;
  } else {
    NEWT(share_array, a);
    *a = *x;
    a->A = bt->a;
    NEWT(share_array, b);
    *b = *x;
    b->A = bt->b;

    share_array sigma, rho;
    sigma = vsub(x, a);
    rho = vsub(y, b);
    share_array sigma_c, rho_c;
    sigma_c = share_reconstruct_channel(sigma, channel); //
    //printf("sigma_c: total send %ld\n", get_total_send());
    rho_c = share_reconstruct_channel(rho, channel); //
    //printf("rho_c: total send %ld\n", get_total_send());

    pa_iter itr_ans = pa_iter_new(ans->A);
    pa_iter itr_sc = pa_iter_new(sigma_c->A);
    pa_iter itr_rc = pa_iter_new(rho_c->A);
    pa_iter itr_a = pa_iter_new(a->A);
    pa_iter itr_b = pa_iter_new(b->A);
    pa_iter itr_c = pa_iter_new(bt->c);

    for (i=0; i<n; i++) {
      share_t tmp;
      share_t sc = pa_iter_get(itr_sc);
      share_t rc = pa_iter_get(itr_rc);
      if (_party == 1) {
        //tmp = LMUL(pa_get(sigma_c->A, i), pa_get(rho_c->A, i), q);
        tmp = LMUL(sc, rc, q);
        //tmp = LMUL(pa_iter_get(itr_sigma_c), pa_iter_get(iter_rho_c), q);
      } else {
        tmp = 0;
      }
      //tmp = MOD(tmp + LMUL(pa_get(a->A,i), pa_get(rho_c->A,i), q));  
      //tmp = MOD(tmp + LMUL(pa_get(b->A,i), pa_get(sigma_c->A,i), q));
      //tmp = MOD(tmp + pa_get(bt->c,i));
      tmp += LMUL(pa_iter_get(itr_a), rc, q);  
      tmp += LMUL(pa_iter_get(itr_b), sc, q);
      tmp = MOD(tmp + pa_iter_get(itr_c));
      //pa_set(ans->A,i,tmp);
      pa_iter_set(itr_ans, tmp);
    }
    pa_iter_flush(itr_ans); pa_iter_free(itr_sc); pa_iter_free(itr_rc);
    pa_iter_free(itr_a); pa_iter_free(itr_b); pa_iter_free(itr_c); 

    pa_free(bt->c);
    share_free(a);  share_free(b);
    share_free(sigma); share_free(rho);
    share_free(sigma_c); share_free(rho_c);
  }
  BeaverTriple_free(bt);


  return ans;
}
#define _vmul vmul
#define vmul(x, y) vmul_channel(x, y, 0)

static void vmul_channel_(share_array a, share_array b, int channel)
{
  if (a == NULL || b == NULL) {
    printf("vmul_: a = %p b = %p\n", a, b);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = vmul_channel(a, b, channel);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _vmul_ vmul_
#define vmul_(x, y) vmul_channel_(x, y, 0)


//////////////////////////////////////////////////
// ビット反転（0,1 以外の値の時は未定義）
//////////////////////////////////////////////////
static share_array vneg(share_array v)
{
  if (v == NULL) {
    printf("vneg: v = %p\n", v);
    return NULL;
  }
  //if (v->q != 2) {
  //  printf("vneg: q = %d\n", v->q);
  //  return NULL;
  //}
  //if (_party >  2) return NULL;
  int n = v->n;
  share_t q = v->q;
  NEWT(share_array, ans);
  *ans = *v;
  ans->A = NULL;
  if (_party > max_partyid(v)) return ans;
  ans->A = pa_new_type(v->n, v->A->w, v->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_v = pa_iter_new(v->A);
  for (int i=0; i<n; i++) {
    if (_party < 2) { // 22ADD, 33ADD, SHAMIR で動作
      //pa_set(ans->A, i, MOD(1 - pa_get(v->A,i)));
      pa_iter_set(itr_ans, MOD(1 - pa_iter_get(itr_v)));
    } else {
      //pa_set(ans->A, i, MOD(0 - pa_get(v->A,i)));
      pa_iter_set(itr_ans, MOD(0 - pa_iter_get(itr_v)));
    }
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_v);
  return ans;
}
#define _vneg vneg

static void vneg_(share_array v)
{
  if (v == NULL) {
    printf("vneg_: v = %p\n", v);
    return;
  }
  //if (v->q != 2) {
  //  printf("vneg_: q = %d\n", v->q);
  //  return;
  //}
  //if (_party >  2) return;
  share_array tmp = vneg(v);
  pa_free(v->A);  *v = *tmp;  free(tmp);
}
#define _vneg_ vneg_

static share_t GF_mul(share_t a, share_t b, share_t irr_poly);

static share_array smul(share_t s, share_array a) // s は公開値
{
  if (a == NULL) {
    printf("smul: a = %p\n", a);
    return NULL;
  }
  //if (_party >  2) return NULL;
  int n = a->n;
  share_t q = a->q;
  NEWT(share_array, ans);
  *ans = *a;
//  printf("smul s = %d\n", s);
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(a->n, a->A->w, a->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_a = pa_iter_new(a->A);
  for (int i=0; i<n; i++) {
  //  printf("i=%d x = %d -> %d\n", i, pa_get(a->A, i), LMUL(s, pa_get(a->A, i), q));
    //pa_set(ans->A, i, LMUL(s, pa_get(a->A, i), q));
    if (ans->irr_poly) {
      share_t c;
      c = GF_mul(s, pa_iter_get(itr_a), ans->irr_poly);
      pa_iter_set(itr_ans, c);
    } else {
      pa_iter_set(itr_ans, LMUL(s, pa_iter_get(itr_a), q));
    }
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a);
  return ans;
}
#define _smul smul

static void smul_(share_t s, share_array a)
{
  if (a == NULL) {
    printf("smul_: a = %p\n", a);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = smul(s, a);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}
#define _smul_ smul_

static share_array smod(share_t s, share_array a) // s は公開値
{
  if (a == NULL) {
    printf("smod: a = %p\n", a);
    return NULL;
  }
  //if (_party >  2) return NULL;
  int n = a->n;
  share_t q = a->q;
  NEWT(share_array, ans);
  *ans = *a;
//  printf("smul s = %d\n", s);
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;
  ans->A = pa_new_type(a->n, a->A->w, a->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  pa_iter itr_a = pa_iter_new(a->A);
  for (int i=0; i<n; i++) {
  //  printf("i=%d x = %d -> %d\n", i, pa_get(a->A, i), LMUL(s, pa_get(a->A, i), q));
    //pa_set(ans->A, i, pa_get(a->A, i) % s);
    pa_iter_set(itr_ans, pa_iter_get(itr_a) % s);
  }
  pa_iter_flush(itr_ans); pa_iter_free(itr_a);
  return ans;
}

static void smod_(share_t s, share_array a)
{
  if (a == NULL) {
    printf("smod_: a = %p\n", a);
    return;
  }
  //if (_party >  2) return;
  share_array tmp = smod(s, a);
  pa_free(a->A);  *a = *tmp;  free(tmp);
}


/////////////////////////////////
// 論理演算
// 入力は 0, 1 のみ
/////////////////////////////////
_ AND_channel(_ a, _ b, int channel)
{
  if (a == NULL || b == NULL) {
    printf("AND: a = %p b = %p\n", a, b);
    return NULL;
  }
  //if (a->q != 2 || b->q != 2) {
  //  printf("AND: a->q = %d b->q = %d\n", a->q, b->q);
  //  return NULL;
  //}
  //if (_party >  2) return NULL;
  return vmul_channel(a, b, channel);
}
#define AND(a, b) AND_channel(a, b, 0)

_ OR_channel(_ a, _ b, int channel)
{
  if (a == NULL || b == NULL) {
    printf("OR: a = %p b = %p\n", a, b);
    return NULL;
  }
  //if (a->q != 2 || b->q != 2) {
  //  printf("OR: a->q = %d b->q = %d\n", a->q, b->q);
  //  return NULL;
  //}
  //if (_party >  2) return NULL;
  _ ap = vneg(a);
  _ bp = vneg(b);
  _ ans = AND_channel(ap, bp, channel);
  vneg_(ans);
  _free(ap);
  _free(bp);
  return ans;
}
#define OR(a, b) OR_channel(a, b, 0)

_ XOR2(_ a, _ b)
{
  if (a == NULL || b == NULL) {
    printf("XOR2: a = %p b = %p\n", a, b);
    return NULL;
  }
  if (a->q != 2 || b->q != 2) {
    printf("XOR2: a->q = %d b->q = %d\n", a->q, b->q);
    return NULL;
  }
  _ ans = vadd(a, b);
  return ans;
}

_ XOR_channel(_ a, _ b, int channel)
{
  if (a == NULL || b == NULL) {
    printf("XOR: a = %p b = %p\n", a, b);
    return NULL;
  }
  if (a->q != b->q) {
    printf("XOR: a->q = %d b->q = %d\n", a->q, b->q);
    return NULL;
  }
  if (a->q == 2) return vadd(a, b);
  //if (_party >  2) return NULL;
  _ ans = vadd(a, b);
  _ c = vmul_channel(a, b, channel); // TODO 効率化可能
  smul_(2, c);
  vsub_(ans, c);
  _free(c);
  return ans;
}
#define XOR(a, b) XOR_channel(a, b, 0)


_ AND_rec_channel(_ x, int n, int channel)
{
  if (x == NULL) {
    printf("AND_rec: x = %p\n", x);
    return NULL;
  }
  int k = len(x) / n;
  if (k == 1) {
    return _dup(x);
  }
  _ first_half  = _slice(x, 0, (k/2)*n);
  _ second_half = _slice(x, (k/2)*n, (k/2)*2*n);
  _ a1 = AND_rec_channel(first_half, n, channel);
  _ a2 = AND_rec_channel(second_half, n, channel);
  _free(first_half); _free(second_half);
  _ ans = AND_channel(a1, a2, channel);
  _free(a1); _free(a2);
  if (k % 2 == 1) {
    _ rest = _slice(x, (k/2)*2*n, k*n);
    _ atmp = AND_channel(ans, rest, channel);
    _free(ans); _free(rest);
    ans = atmp;
  }
  //printf("AND "); _print(ans);
  return ans;
}
#define AND_rec(x, n) AND_rec_channel(x, n, 0)


static share_array Perm_ID2_type(int n, share_t q, int pa_type)
{
  //if (_party >  2) return NULL;
  NEWT(share_array, ans);
  ans->n = n;
  ans->q = q;
  ans->type = SHARE_T_22ADD;
  ans->irr_poly = 0;
  ans->A = NULL;
  if (_party > 2) return ans;
  int w = blog(q-1)+1;
  ans->A = pa_new_type(n, w, pa_type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  for (int i=0; i<ans->n; i++) {
    if (_party < 2) {
      //pa_set(ans->A, i, i);
      pa_iter_set(itr_ans, i);
    } else {
      //pa_set(ans->A, i, 0);
    }
  }
  pa_iter_flush(itr_ans);
  return ans;
}
#define Perm_ID2(n, q) Perm_ID2_type(n, q, PA_PACK)


static share_array Perm_ID(share_array a)
{
  if (a == NULL) {
    printf("Perm_ID: a = %p\n", a);
    return NULL;
  }
  //if (_party >  2) return NULL;
  if (a->q < a->n) {
    printf("Perm_ID: n = %d q = %d", a->n, (int)a->q);
  }
  NEWT(share_array, ans);
  *ans = *a;
  //ans->n = a->n;
  //ans->q = a->q;
  ans->A = NULL;
  if (_party > max_partyid(a)) return ans;

  ans->A = pa_new_type(a->n, a->A->w, a->A->type);
  pa_iter itr_ans = pa_iter_new(ans->A);
  for (int i=0; i<ans->n; i++) {
    if (_party < 2) {
      //pa_set(ans->A, i, i);
      pa_iter_set(itr_ans, i);
    }
  }
  pa_iter_flush(itr_ans);
  return ans;
}


///////////////////////////////////////////////////
// 共有乱数の配列を作る
///////////////////////////////////////////////////
static _ shared_random_channel_type(int n, share_t q, int party1, int party2, int channel, int pa_type)
{
  _ ans;
  if (_party <= 0) {
    ans = share_const_type2(n, 0, q, SHARE_T_ADDITIVE, pa_type);
    return ans;
  }
  if (_party != party1 && _party != party2) return NULL;

  ans = share_const_type2(n, 0, q, SHARE_T_ADDITIVE, pa_type);
  int pair = party1 + party2 - _party;
  for (int i=0; i<n; i++) {
    pa_set(ans->A, i, RANDOM(mt_[pair][channel], q));
  }
  return ans;
}
#define shared_random_channel(n, q, party1, party2, channel) shared_random_channel_type(n, q, party1, party2, channel, PA_PACK)
//#define shared_random(n, q, p1, p2) share_randomize(n, q, p1, p2, 0)
#define shared_random(n, q, p1, p2) shared_random_channel(n, q, p1, p2, 0)


#include "compare.h"
#include "func.h"
#include "dshare.h"
#include "field.h"
#include "unitv.h"
#include "shamir.h"
#include "rss.h"

#endif
