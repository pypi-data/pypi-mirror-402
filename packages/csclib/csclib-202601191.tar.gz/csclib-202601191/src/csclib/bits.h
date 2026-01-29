// typedef xxx pa_t;

#ifndef _BITS_H
 #define _BITS_H

//#define NEW_PA

//#define FAST_BIT

typedef long i64;
typedef unsigned long u64;
typedef unsigned char uchar;

#ifdef FAST_BIT
 //#define logQ 5
 //typedef unsigned int bitvec_t;
 #define logQ 6
 typedef u64 bitvec_t;
#else
 #define logQ 6
 typedef u64 bitvec_t;
#endif

#define _Q (1L<<logQ) // 小ブロック(1ワード)のサイズ

#define ID_PACKEDARRAY 0x18
#define ID_SHARE 0x1C
#define ID_SCSA 0x1D

/////////////////////////////////////////////////////
// 整数の桁数を求める
// to store an integer in [0,x-1], we need blog(x-1)+1 bits
/////////////////////////////////////////////////////
static int blog(u64 x)
{
int l;
  l = -1;
  while (x>0) {
    x>>=1;
    l++;
  }
  return l;
}



static int setbit(bitvec_t *B, i64 i,int x)
{
  i64 j,l;

  j = i / _Q;
//  l = i & (_Q-1);
  l = _Q - (i & (_Q-1)) -1; // !!!
  if (x==0) B[j] &= (~(1L<<(l)));
  else if (x==1) B[j] |= (1L<<(l));
  else {
    printf("error setbit x=%d\n",x);
    exit(1);
  }
  return x;
}

static int getbit(bitvec_t *B, i64 i)
{
  i64 j,l;

  j = i >> logQ;
//  l = i & (_Q-1);
  l = _Q - (i & (_Q-1)) -1; // !!!
  return (B[j] >> (l)) & 1;
}

static u64 getbits(bitvec_t *B, i64 i, int d)
{
  u64 x,z;

  if (d == 0) return 0;
  B += (i >>logQ);
  i &= (_Q-1);
  if (i+d <= _Q) {
    x = B[0];
    x <<= i;
    x >>= (_Q-d);  // Q==64, d==0 だと動かない
  } else {
    x = B[0] << i;
    x >>= _Q-d;
    z = B[1] >> (_Q-(i+d-_Q));
    x += z;
  }
  return x;
}

static void setbits(bitvec_t *B, i64 i, int d, u64 x)
{
  u64 y,m;
  int d2;

  B += (i>>logQ);
  i &= (_Q-1);

  while (i+d > _Q) {
    d2 = _Q-i; // x の上位 d2 ビットを格納
    y = x >> (d-d2);
    m = (1<<d2)-1;
    *B = (*B & (~m)) | y;
    B++;  i=0;
    d -= d2;
    x &= (1L<<d)-1; // x の上位ビットを消去
  }
  m = (1L<<d)-1;
  y = x << (_Q-i-d);
  m <<= (_Q-i-d);
  *B = (*B & (~m)) | y;

}

static void writeuint(int k, i64 x, FILE *f)
{
  int i;
  for (i=k-1; i>=0; i--) {
    fputc(x & 0xff,f); // little endian
    x >>= 8;
  }
}

static u64 getuint(uchar *s, i64 i, i64 w)
{
  u64 x;
  i64 j;
  s += i*w;
  x = 0;
  for (j=0; j<w; j++) {
    x += ((u64)(*s++)) << (j*8);
  }
  return x;
}

static void putuint(uchar *s, i64 i, i64 x, i64 w)
{
  i64 j;
  s += i*w;
  for (j=0; j<w; j++) {
    *s++ = x & 0xff;
    x >>= 8;
  }
}

typedef struct {
  i64 n;
  int w;
  bitvec_t *B;

  int type; // ビットの圧縮方法

  // for iterator
//  bitvec_t *p;
//  bitvec_t x;
//  int k;
}* packed_array;

#define PA_PACK 0
//#define PA_BIT 1
#define PA_SIGN 2
//#define PA_ 3
#define PA_RAW 4

/******************************************************************
 * bit の詰め込み方（予定）
 * 1 bit -> 1 bit（加算は xor で計算）
 * k bit -> k+1 bit で格納（1 bit は比較用のビット）
 * W bit のワードには W/(k+1) 個（切り捨て）の値を格納
******************************************************************/


static int pa_W(i64 w) // 1要素を表現するビット数
{
  if (w <= 0 || w >= _Q) {
    printf("pa_W: w = %ld\n", w);
    return -1;
  }
  if (w == 1) return 1;
  return w+1;
}


static i64 pa_size(packed_array p)
{
  i64 n = p->n;
  i64 w = p->w;
  i64 num_words;

  switch(p->type) {
    case PA_PACK:
    //case PA_BIT:
      num_words = (n / _Q)*w + ((n % _Q)*w + _Q-1) / _Q;
      break;
    case PA_SIGN:
      {
        i64 m;
        m = _Q / pa_W(p->w); // 1ワードに格納できる要素数
        num_words = (n + m-1) / m; // 格納に必要なワード数
      }
      break;
    case PA_RAW:
      num_words = n; // 1要素１ワード
      break;
    default:
      printf("pa_size: type=%d\n", p->type);
      break;
  }

  return num_words*sizeof(bitvec_t);
}


static packed_array pa_new_type(i64 n, int w, int type)
{
  i64 num_words;

  NEWT(packed_array, p);
  p->n = n;  p->w = w;  p->type = type;
  //x = (n / _Q)*w + ((n % _Q)*w + _Q-1) / _Q;
  num_words = pa_size(p);
  if (num_words == 0) num_words = 1; // w == 0 の時にも 1 ワードだけメモリを確保する．
  NEWA(p->B, bitvec_t, num_words);
  //for (i=0; i<x; i++) p->B[i] = 0;
  memset(p->B, 0, num_words*sizeof(bitvec_t));

  return p;
}
#define pa_new(n, w) pa_new_type(n, w, PA_PACK)


static packed_array pa_dup(packed_array a)
{
  i64 num_words;

//  i64 n = a->n;
//  i64 w = a->w;

#ifdef FAST_BIT
  w = _Q;
#endif

  NEWT(packed_array, p);
  //p->n = n;  p->w = w;
  *p = *a;
//  x = (n / _Q)*w + ((n % _Q)*w + _Q-1) / _Q;
  num_words = pa_size(p);
  NEWA(p->B, bitvec_t, num_words);
  memcpy(p->B, a->B, num_words*sizeof(bitvec_t));

  return p;
}

static void pa_free(packed_array p)
{
  if (p == NULL) return;
  free(p->B);
  free(p);
}

static void pa_free_map(packed_array p)
{
  //free(p->B);
  free(p);
}

static pa_t pa_get(packed_array p, i64 i)
{
  int w;
  bitvec_t *B;

//#ifdef FAST_BIT
//  return (u64)p->B[i];
//#endif
//  if (p->w == 8*sizeof(p->B[0])) {
//    return (u64)p->B[i];
//  }
  switch (p->type) {
    case PA_RAW: 
      return (pa_t)p->B[i];
    case PA_PACK:
      B = p->B;
      if (p->w == 1) return (pa_t)getbit(B,i);
      return (pa_t)getbits(B,i*p->w,p->w);
    case PA_SIGN:
      {
        i64 w = p->w;
        i64 W = pa_W(w);
        i64 m = _Q / W;
        i64 iq = i / m;
        i64 ir = i % m;
        B = p->B + iq;
        u64 z = getbits(B,ir * W + (W-w), w);
        return (pa_t)z;        
      }
    default:
      printf("pa_get: type=%d\n", p->type);
      break;
  }
}

static void pa_set(packed_array p, i64 i, pa_t x)
{
  int w;
  bitvec_t *B;

#if 0
  if (x < 0 || (long)x > (1L<<p->w)) {
    printf("pa_set: x=%ld w=%d\n",(long)x,p->w);
  }
  if (i < 0 || i >= p->n) {
    printf("pa_set: i=%ld n=%ld\n",i,p->n);
  }
#endif

  switch (p->type) {
    case PA_RAW: 
      //p->B[i] = x;
      p->B[i] = x & ((1<<p->w)-1);
      break;
    case PA_PACK:
    //case PA_BIT:
      B = p->B;
      if (p->w == 1) {
        setbit(B,i,x);
        break;
      }
      setbits(B,i*p->w,p->w,x);
      break;
    case PA_SIGN:
      {
        i64 w = p->w;
        i64 W = pa_W(w);
        i64 m = _Q / W;
        i64 iq = i / m;
        i64 ir = i % m;
        B = p->B + iq;
        setbits(B,ir * W, W, x); // 入力は w ビットのはずだがそれより上は 0 と仮定して W ビット書く
      }
      break;
    default:
      printf("pa_set: type=%d\n", p->type);
      break;
  }

}



#define _W (8*sizeof(bitvec_t))


typedef struct pa_iter {
  bitvec_t *p;
  bitvec_t x;
  int k, w;
  int type;

// tmp
  packed_array a;
}* pa_iter;
//typedef struct pa_iter pa_iter_;

#define NEWITER(var, for) pa_iter var = pa_iter_new(for->A);

pa_iter pa_iter_new(packed_array p)
{
  NEWT(pa_iter, itr);
  if (p == NULL) {
    itr->p = NULL;
    itr->x = 0;
    itr->k = 0;
    itr->type = -1;
    return itr;
  }
  itr->p = p->B;
  itr->x = 0;
  itr->k = 0;
  itr->type = p->type;

  switch (p->type) {
    case PA_RAW:
      itr->w = 0;
      break;
    case PA_PACK:
    //case PA_BIT:
      itr->w = p->w;
    //  itr->w = 0; // temporary
      break;
    case PA_SIGN:
      itr->w = 0; // temporary
      break;
  }


  itr->a = p;
  return itr;
}

pa_iter pa_iter_pos_new_packed(packed_array p, i64 pos)
{
  NEWT(pa_iter, itr);
  i64 q = (pos*p->w) / _W;
  //printf("p %d W %d\n", (int)(pos*p->w), ((int)W));
  int r = (int)((pos*p->w) & (int)(_W-1));
  //int r2 = ((int)(pos*p->w)) % ((int)W);
  //int r3 = (pos*p->w) - q*W;
  //printf("q %d r %d r2 %d r3 %d\n", (int)q, r, r2, r3);
  itr->p = p->B + q;
  itr->x = *(itr->p)++;
  itr->x <<= r;
  itr->k = _W-r;
  itr->w = p->w;
//  itr->w = 0; // temporary
  itr->type = p->type;

  itr->a = p;
  return itr;
}

pa_iter pa_iter_pos_new(packed_array p, i64 pos)
{
  if (p->type == PA_PACK) return pa_iter_pos_new_packed(p, pos); 

  NEWT(pa_iter, itr);
  itr->p = p->B;
  itr->k = pos;
  itr->w = p->w;
//  itr->w = 0;
  itr->type = p->type;

  itr->a = p;
  return itr;
}


pa_t pa_iter_get_packed(pa_iter itr)
{
  pa_t ans = 0;
  //int w = itr->w;
  int w = itr->a->w; // temporary
  int k = itr->k;
  bitvec_t x = itr->x;
  //printf("x %d\n", x);
  if (k < w) { // ビットが足りない
    bitvec_t x2 = *(itr->p)++;
    //printf("x2 %d\n", x2);
    //printf("x2=%lx\n", x2);
    x += (x2 >> k);
    ans = x >> (_W-w);
    //printf("_W %d\n", _W);
    //printf("x %d\n", x);
    //printf("k %d\n", k);
    //printf("w %d\n", w);
    //printf("ans1 %d\n", ans);
    x = x2 << (w-k);
    k += _W;
  } else {
    ans = x >> (_W-w);
    //printf("ans2 %d\n", ans);
    x <<= w;
  }
  k -= w;

  itr->x = x;
  itr->k = k;

  return ans;
}

pa_t pa_iter_get(pa_iter itr)
{
  if (itr->p == NULL) return 0;
  if (itr->type == PA_PACK) return pa_iter_get_packed(itr); 

  i64 k = itr->k;
  pa_t ans = pa_get(itr->a, k);
  itr->k = k+1;
  return ans;
}

void pa_iter_set_packed(pa_iter itr, pa_t z)
{
  int w = itr->w;
  int k = itr->k;
  bitvec_t x = itr->x;

  if (k + w > _W) { // ビットがあふれる
    x += z >> (k+w-_W);
    *(itr->p)++ = x;
    k -= _W;
    x = 0;
  }
  x += ((bitvec_t)z) << (_W-k-w);
  k += w;
  itr->x = x;
  itr->k = k;
}

void pa_iter_set(pa_iter itr, pa_t z)
{
  if (itr->p == NULL) return;
  if (itr->type == PA_PACK) return pa_iter_set_packed(itr, z); 

  i64 k = itr->k;
  pa_set(itr->a, k, z);
  itr->k = k+1;
}

void pa_iter_free(pa_iter itr)
{
  free(itr);
}

void pa_iter_flush(pa_iter itr)
{
  if (itr->type == PA_PACK) {
    if (itr->w > 0) {
      *(itr->p) = itr->x;
    } else {
      printf("flush: ???\n");
    }
  }
  pa_iter_free(itr);
}


pa_t *pa_unpack_(packed_array p)
{
  i64 n = p->n;
  pa_t *q;
  int w = p->w;
  NEWA(q, pa_t, n);
  bitvec_t *B = p->B;
  bitvec_t x1 = 0;
  int k = 0; // まだ読んでないビット数
  for (i64 i=0; i<n; i++) {
    if (k < w) { // ビットが足りない
      bitvec_t x2 = *B++;
      //printf("x2=%lx\n", x2);
      x1 += x2 >> k;
      q[i] = x1 >> (_W-w);
      x1 = x2 << (w-k);
      k += _W;
    } else {
      q[i] = x1 >> (_W-w);
      x1 <<= w;
    }
    k -= w;
  //  printf("i=%ld k=%d B=%ld x1=%lx\n", i, k, q[i], x1);
  }
  return q;
}

//pa_t *pa_unpack_type(packed_array p, int type)
pa_t *pa_unpack(packed_array p)
{
  if (p->type == PA_PACK) return pa_unpack_(p);
  if (p->type != PA_RAW) {
    printf("pa_unpack: type = %d\n", p->type);
    exit(1);
  }
  i64 n = p->n;
  pa_t *q;
  int w = p->w;
  NEWA(q, pa_t, n);

  for (i64 i=0; i<n; i++) {
    q[i] = pa_get(p, i);
  }

  return q;
}
//#define pa_unpack(p) pa_unpack_type(p, PA_PACK)

packed_array pa_pack_(i64 n, int w, pa_t *q)
{
  packed_array p = pa_new(n, w);

  bitvec_t *B = p->B;
  bitvec_t x1 = 0;
  int k = 0; // 既に入っているビット数
  for (i64 i=0; i<n; i++) {
    //printf("i=%ld k=%d A=%ld x1=%lx\n", i, k, q[i], x1);
    if (k + w > _W) { // ビットがあふれる
      x1 += ((bitvec_t)q[i]) >> (k+w-_W);
      *B++ = x1;
      x1 = ((bitvec_t)q[i]) << (2*_W-k-w);
      k += w-_W;
    } else {      
      x1 += ((bitvec_t)q[i]) << (_W-k-w);
      k += w;
    }
  }
  if (k > 0) {
    *B++ = x1;
  }
  return p;
}

packed_array pa_convert(packed_array a, int type)
{
  int n = a->n;
  packed_array ans = pa_new_type(n, a->w, type);
  pa_iter itr_a = pa_iter_new(a);
  pa_iter itr_ans = pa_iter_new(ans);
  for (int i=0; i<n; i++) pa_iter_set(itr_ans, pa_iter_get(itr_a));
  pa_iter_flush(itr_ans);
  pa_iter_free(itr_a);
  return ans;
}

packed_array pa_pack_type(i64 n, int w, pa_t *q, int type)
{
  if (type == PA_PACK) return pa_pack_(n, w, q);
  if (type != PA_RAW) {
    printf("pa_pack: type = %d\n", type);
    exit(1);
  }
//  packed_array p = pa_new(n, w);
  packed_array p = pa_new_type(n, w, PA_RAW);

  bitvec_t *B = p->B;
  bitvec_t x1 = 0;
  int k = 0; // 既に入っているビット数
  for (i64 i=0; i<n; i++) {
    pa_set(p, i, q[i]);
  }
  return p;
}
#define pa_pack(n, w, q) pa_pack_type(n, w, q, PA_PACK)







#undef _W





static packed_array pa_dup_type(packed_array a, int type)
{
  if (a->type == type) return pa_dup(a);

  packed_array b = pa_new_type(a->n, a->w, type);

  pa_iter itr_a = pa_iter_new(a);
  pa_iter itr_b = pa_iter_new(b);
  i64 n = a->n;
  for (i64 i=0; i<n; i++) {
    pa_iter_set(itr_b, pa_iter_get(itr_a));
  }
  pa_iter_flush(itr_b); pa_iter_free(itr_a);
  return b;
}






i64 pa_write(packed_array pa, FILE *f)
{
  i64 size = 0;
  writeuint(1,ID_PACKEDARRAY,f);
  writeuint(sizeof(pa->n), pa->n, f);
  writeuint(sizeof(pa->w), pa->w, f);
  size += 1 + sizeof(pa->n) + sizeof(pa->w);

  if (pa->type == PA_PACK) {
    i64 num_words = (pa->n / _Q)*pa->w + ((pa->n % _Q)*pa->w + _Q-1) / _Q;
    for (i64 i=0; i<num_words; i++) {
      writeuint(sizeof(pa->B[0]), pa->B[i], f); size += sizeof(pa->B[0]);
    }
  } else {
#if 0
    packed_array tmp = pa_new_type(pa->n, pa->w, PA_PACK);
    pa_iter itr_pa = pa_iter_new(pa);
    pa_iter itr_tmp = pa_iter_new(tmp);
    i64 n = pa->n;
    for (i64 i=0; i<n; i++) {
      pa_iter_set(itr_tmp, pa_iter_get(itr_pa));
    }
    pa_iter_flush(itr_tmp); pa_iter_free(itr_pa);
    i64 num_words = pa_size(tmp);
    for (i64 i=0; i<num_words; i++) {
      writeuint(sizeof(tmp->B[0]), tmp->B[i], f); size += sizeof(tmp->B[0]);
    }
    pa_free(tmp);
#else
    packed_array tmp = pa_dup_type(pa, PA_PACK);
    i64 num_words = pa_size(tmp);
    for (i64 i=0; i<num_words; i++) {
      writeuint(sizeof(tmp->B[0]), tmp->B[i], f); size += sizeof(tmp->B[0]);
    }
    pa_free(tmp);
#endif
  }

  return size;
}

packed_array pa_read(uchar **map)
{
  i64 x;
  uchar *p;

  p = *map;

  x = getuint(p,0,1);  p += 1;
  if (x != ID_PACKEDARRAY) {
    printf("pa_read: id = %ld is not supported.\n", x);
    exit(1);
  }

  NEWT(packed_array, pa);

  pa->n = getuint(p,0,sizeof(pa->n));  p += sizeof(pa->n);
  pa->w = getuint(p,0,sizeof(pa->w));  p += sizeof(pa->w);
  pa->type = PA_PACK;
  pa->B = (bitvec_t *)p;
  x = (pa->n / _Q)*pa->w + ((pa->n % _Q)*pa->w + _Q-1) / _Q;
  p += x * sizeof(pa->B[0]);

  *map = p;

  return pa;
}

void pa_print(packed_array a)
{
  for (int i=0; i<a->n; i++) {
    printf("%ld ", (long)pa_get(a, i));
  }
  printf("\n");
}

#undef logQ
#undef _Q


#endif
