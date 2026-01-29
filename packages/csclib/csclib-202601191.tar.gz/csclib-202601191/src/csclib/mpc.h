////////////////////////////////////////////////////////
// MPC全般の処理（シェアに関係することは書かない）
////////////////////////////////////////////////////////

#ifndef _MPC_H
 #define _MPC_H

#include <pthread.h>
#include "comm.h"

#define MAX_PARTIES 4
#define MAX_CHANNELS 10

//#ifndef NC
// #define NC 1
//#endif
//#define NP (NC*2+1)




typedef void *(*thread_func)(void *);

typedef struct parties {
  char *addr;
  int port;
}* parties;

extern parties *_Parties;
extern int _party;

#ifndef _Parties_VAR
 #define _Parties_VAR
 parties *_Parties;
 int _num_parties;
 int _party = 0;
#endif

//extern void* BT_tbl[];
//extern void* PRE_OF_tbl[];
//extern void* PRE_B2A_tbl[];

void bt_tbl_init(void);
void of_tbl_init(void);
void b2a_tbl_init(void);
void bt_tbl_read(int channel, char *fname);
void of_tbl_read(int d, int channel, char *fname);
void b2a_tbl_read(int channel, char *fname);
void onehot_tbl_init(void);
void onehot_tbl_read(int d, int xor, int channel, char *fname);
void onehot_shamir_tbl_read(int d, int channel, char *fname);
void onehot_shamir3_tbl_read(int d, share_t irr_poly, int channel, char *fname);
void ds_tbl_read(int channel, int n, int bs, int inverse, char *fname);
void GF_tbl_read(int channel, share_t irr_poly, char *fname);
void shamir3_revert_tbl_read(int d, share_t irr_poly, int channel, char *fname);
void uv_tbl_init(void);
void uv_tbl_read(int channel, int n, int old_q, int new_q, char *fname);
void onehot_rss_tbl_read(int d, share_t irr_poly, int channel, char *fname);

#define scmp(p, q) strncasecmp(p, q, strlen(q))

extern unsigned long MT_init[4][5];

parties* read_config(FILE *fin)
{
  char buf[1000];
  char fname[1000];
  int channel;
  parties *P;
//  P = (parties *)malloc(MAX_PARTIES*sizeof(*P));
  NEWA(P, parties, MAX_PARTIES);
  for (int i=0; i<MAX_PARTIES; i++) P[i] = NULL;

  if (fgets(buf, 1000, fin) == NULL) goto end;
  while (1) {
    if (scmp(buf, "[options]") == 0) {
      int x;
      while (1) {
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %999s %d", fname, &x) != 2) break;
        if (scmp(fname, "parties") == 0) {
          if (x > MAX_PARTIES) {
            printf("MAX_PARTIES = %d parties = %d\n", MAX_PARTIES, x);
            exit(1);
          }
          _opt.parties = x;
          printf("number of parties = %d\n", x);
          _num_parties = _opt.channels;
        } else if (scmp(fname, "channels") == 0) {
          if (x > MAX_CHANNELS) {
            printf("MAX_CHANNELS = %d parties = %d\n", MAX_CHANNELS, x);
            exit(1);
          }
          _opt.channels = x;
          printf("number of channels = %d\n", x);
        } else if (scmp(fname, "comm_no_delay") == 0) {
          _opt.comm_no_delay = x;
          printf("opt.comm_no_delay = %d\n", x);
        } else if (scmp(fname, "warn_precomp") == 0) {
          _opt.warn_precomp = x;
          printf("opt.warn_precomp = %d\n", x);
        } else if (scmp(fname, "send_queue") == 0) {
          _opt.send_queue = x;
          printf("opt.send_queue = %d\n", x);
        } else if (scmp(fname, "oram_check_overflow") == 0) {
          _opt.oram_check_overflow = x;
          printf("opt.oram_check_overflow = %d\n", x);
        } else {
          printf("??? %s\n", fname);
        }
      }
    }
    if (_party == -1) {
      if (fgets(buf, 1000, fin) == NULL) break;
      continue;
    }
    if (scmp(buf, "[parties]") == 0) {
      int i = 0;
      while (i < MAX_PARTIES) {
        char addr[100];
        int port;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue; // skip comments
        //if (buf[0] == '[') continue; // skip
        if (sscanf(buf, " %99s %d", addr, &port) != 2) break;
        P[i] = (parties)malloc(sizeof(*P[i]));
        P[i]->addr = strdup(addr);
        P[i]->port = port;
        printf("party %d %s:%d\n", i, addr, port);
        i++;
      }
      if (i < _opt.parties) {
        printf("warning: opt.parties = %d i = %d\n", _opt.parties, i);
      }
    } else if (scmp(buf, "[mt_seeds]") == 0) { // TODO: チャンネルごとに分ける
      unsigned long init[5];
      int party;
      while (1) {
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %ld %ld %ld %ld %ld", &party, &init[0], &init[1], &init[2], &init[3], &init[4]) != 6) break;
        if (party < 0 || party > 3) {
          printf("error party %d\n", party);
          exit(1);
        }
        for (int i=0; i<5; i++) MT_init[party][i] = init[i];
      }
    } else if (scmp(buf, "[pre_bt]") == 0) {
      while (1) {
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %s", &channel, fname) != 2) break;
        if (channel >= _opt.channels) {
          continue; // 不要なテーブルは読み飛ばす
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          bt_tbl_read(channel, fname);
          printf("BT_tbl %d %s\n", channel, fname);
        }
      }
    } else if (scmp(buf, "[pre_of]") == 0) {
      while (1) {
        int d;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %d %s", &d, &channel, fname) != 3) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          of_tbl_read(d, channel, fname);
          printf("PRE_OF_tbl bits=%d channel=%d %s\n", d, channel, fname);
        }
      }
    } else if (scmp(buf, "[pre_b2a]") == 0) {
      while (1) {
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %s", &channel, fname) != 2) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d NC %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          b2a_tbl_read(channel, fname);
          printf("PRE_B2A_tbl %d %s\n", channel, fname);
        }
      }
    } else if (scmp(buf, "[pre_onehot]") == 0) {
      while (1) {
        int d, xor;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %d %d %s", &d, &xor, &channel, fname) != 4) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          onehot_tbl_read(d, xor, channel, fname);
          printf("PRE_OH_tbl bits=%d xor=%d channel=%d %s\n", d, xor, channel, fname);
        }
      }
    } else if (scmp(buf, "[pre_onehot_shamir]") == 0) {
      while (1) {
        int d, xor;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %d %s", &d, &channel, fname) != 3) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        onehot_shamir_tbl_read(d, channel, fname);
        printf("PRE_OHS_tbl bits=%d channel=%d %s\n", d, channel, fname);
      }
    } else if (scmp(buf, "[pre_onehot_shamir3]") == 0) {
      while (1) {
        int d, xor;
        share_t irr_poly;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %x %d %s", &d, &irr_poly, &channel, fname) != 4) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        onehot_shamir3_tbl_read(d, irr_poly, channel, fname);
        printf("PRE_OHS3_tbl bits=%d irr_poly=%x channel=%d %s\n", d, irr_poly, channel, fname);
      }
    } else if (scmp(buf, "[pre_onehot_rss]") == 0) {
      while (1) {
        int d, xor;
        share_t irr_poly;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %x %d %s", &d, &irr_poly, &channel, fname) != 4) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        onehot_rss_tbl_read(d, irr_poly, channel, fname);
        printf("PRE_OHR_tbl bits=%d irr_poly=%x channel=%d %s\n", d, irr_poly, channel, fname);
      }
    } else if (scmp(buf, "[pre_shamir3_revert]") == 0) {
      while (1) {
        int d, xor;
        share_t irr_poly;
        if (fgets(buf, 1000, fin) == NULL) goto end;
      //  if (buf[0] == '#') continue;
        if (buf[0] == '#') break;
        if (sscanf(buf, " %d %x %d %s", &d, &irr_poly, &channel, fname) != 4) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        shamir3_revert_tbl_read(d, irr_poly, channel, fname);
        printf("PRE_RE_tbl bits=%d irr_poly=%x channel=%d %s\n", d, irr_poly, channel, fname);
      }
    } else if (scmp(buf, "[pre_ds]") == 0) {
      while (1) {
        int n, bs, inverse;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %d %d %d %s", &n, &bs, &inverse, &channel, fname) != 5) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          ds_tbl_read(channel, n, bs, inverse, fname);
          printf("PRE_DS_tbl n=%d bs=%d inverse=%d channel=%d %s\n", n, bs, inverse, channel, fname);
        }
      }
    } else if (scmp(buf, "[pre_uv]") == 0) {
      while (1) {
        int n, old_q, new_q, channel;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %d %d %d %d %s", &n, &old_q, &new_q, &channel, fname) != 5) break;
        if (channel > _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        uv_tbl_read(channel, n, old_q, new_q, fname);
        printf("PRE_UV_tbl %d %s\n", channel, fname);
      } 
    } else if (scmp(buf, "[pre_gf]") == 0) {
      while (1) {
        share_t irr_poly;
        if (fgets(buf, 1000, fin) == NULL) goto end;
        if (buf[0] == '#') continue;
        if (sscanf(buf, " %x %d %s", &irr_poly, &channel, fname) != 3) break;
        if (channel >= _opt.channels) {
          continue;
          //printf("error channel %d MAX_CHANNELS %d\n", channel, MAX_CHANNELS);
          //exit(1);
        }
        if (_party <= 2) {
          GF_tbl_read(channel, irr_poly, fname);
          printf("PRE_GF_tbl irr_poly=%x channel=%d %s\n", irr_poly, channel, fname);
        }
      }
    } else if (buf[0] == '#') { // skip comments
      if (fgets(buf, 1000, fin) == NULL) break;
    } else {
      if (fgets(buf, 1000, fin) == NULL) break;
    }
  }
  end:;
  if (_party == -1) {
    _opt.warn_precomp = 0;
  }
  return P;
}

static parties* party_read(void)
{
  if (_party == -1) {
    //int num_parties = 1;
   // parties *P;
   // P = (parties *)malloc(MAX_PARTIES*sizeof(*P));
   // for (int i=0; i<MAX_PARTIES; i++) P[i] = NULL;
    _opt.parties = 1;
    //return P;
  }

  FILE *fin;
//  comm C;
  char buf[1000];
//  char dest_addr[100];
//  int  dest_port;
//  int  recv_port;
  int  i;

  _opt.parties = 3; // default
  _opt.channels = 1; // default

  fin = fopen("config.txt", "r");
  if (fin == NULL && _party >= 0) {
    printf("cannot open config.txt\n");
    exit(1);  
  }
#if 0
  i = 0;
  while (i < num_parties) {
    char addr[100];
    int port;
    if (fgets(buf, 1000, fin) == NULL) break;
    if (buf[0] == '#') continue; // skip comments
    if (buf[0] == '[') continue; // skip
    sscanf(buf, " %s %d", addr, &port);
  //  NEW(P[i], 1);
    P[i] = (parties)malloc(sizeof(**P));
    P[i]->addr = strdup(addr);
    P[i]->port = port;
    printf("party %d %s:%d\n", i, addr, port);
    i++;
  }
#endif
  parties *P = read_config(fin);
  fclose(fin);
  _num_parties = _opt.parties; // 将来的には削除
  return P;
}

static void party_free(parties *P, int num_parties)
{
  for (int i=0; i<MAX_PARTIES; i++) {
    if (P[i]) {
      free(P[i]->addr);
      free(P[i]);
    }
  }
  free(P);
}

comm *_C;
#define TO_PARTY1 1
#define TO_PARTY2 2
#define FROM_PARTY1 1
#define FROM_PARTY2 2
#define TO_PARTY3 3
#define FROM_PARTY3 3
#define TO_SERVER 0
#define FROM_SERVER 0
#define TO_PAIR (3-_party)
#define FROM_PAIR (3-_party)

// int send_queue_idx[NP+NC];
// char *send_queue[NP+NC];
int *_send_queue_idx;
char **_send_queue;

typedef struct thread_param {
  pthread_t th;
  thread_func func; // 不要?
  void *args;       // 不要?
}* thread_param;

thread_param thread_new(thread_func func, void *args)
{
  NEWT(thread_param, param);
  param->func = func;
  param->args = args;

  int ret = pthread_create(&param->th, NULL, func, args);
  if (ret != 0) {
    printf("thread_new: ret %d\n", ret);
    exit(1);
  }
  return param;
}

void thread_end(thread_param param)
{
  int ret;
  ret = pthread_join(param->th, NULL);
  if (ret != 0) {
    printf("thread_end: ret %d\n", ret);
  }
  free(param);
}

typedef struct comm_init_args {
  int server;
  int port;
  char *dest_name;
  comm ans;
}* comm_init_args;

void *comm_init_thread(void *arg_)
{
  comm_init_args arg = (comm_init_args)arg_;
  if (arg->server) {
    arg->ans = comm_init_server(arg->port);
  } else {
    arg->ans = comm_init_client(arg->dest_name, arg->port);
  }
  return NULL;
}

void precomp_tables_new(void); 
void precomp_tables_free(void); 
void PRG_initialize(int num_parties);
void PRG_free(void);


static void mpc_start(void)  // roundの追記
{
  precomp_tables_new();


  printf("party %d\n", _party);
//  _Parties = party_read();
  if (_party < 0) { // _party == -1 のときにconfigを読んでいる理由を忘れた
    _opt.parties = 1;
    _opt.channels = 1;
    PRG_initialize(1);
    //_Parties = party_read(0);
    parties *P;
    NEWA(P, parties, MAX_PARTIES);
    for (int i=0; i<MAX_PARTIES; i++) P[i] = NULL;
    _Parties = P;
    return;
  }
  _Parties = party_read();

  int num_parties = _opt.parties;
  int num_channels = _opt.channels;

  NEWA(_C, comm, num_channels*num_parties);
  for (int i=0; i<num_channels*num_parties; i++) _C[i] = NULL;


  //thread_param params[NP+1+NC];
  thread_param *params;
  NEWA(params, thread_param, num_channels*num_parties);

  //struct comm_init_args args[NP+1+NC];
  struct comm_init_args *args;
  NEWA(args, struct comm_init_args, num_channels*num_parties);

  if (_party == 0) { // P0 は他のパーティに対してサーバになる
    for (int j=1; j<num_parties; j++) {
      for (int i=0; i<num_channels; i++) {
        int x = i*num_parties+j;
        args[x].server = 1;
        args[x].port = _Parties[0]->port + x;
        params[x] = thread_new(comm_init_thread, &args[x]);
        //printf("b i=%d x=%d port %d\n", i, x, args[x].port);
      }
    }
  } else {
    for (int i=0; i<num_channels; i++) { // P0 へ接続
      int x = i*num_parties+TO_SERVER;
      args[x].server = 0;
      args[x].dest_name = _Parties[0]->addr;
      args[x].port = _Parties[0]->port + i*num_parties+_party;
      params[x] = thread_new(comm_init_thread, &args[x]);
      //printf("c i=%d x=%d server %s port %d\n", i, x, args[x].dest_name, args[x].port);
      if (_party != num_parties-1) { // 最後のパーティ以外は，次のパーティに対してサーバになる
        int x = i*num_parties + _party+1;
        args[x].server = 1;
        args[x].port = _Parties[_party]->port + x;
        params[x] = thread_new(comm_init_thread, &args[x]);
        //printf("d i=%d x=%d port %d\n", i, x, args[x].port);
      } 
      if (_party == 1 && num_parties > 3) { // P1 は最後のパーティに対しサーバになる
        int x = i*num_parties + num_parties-1; // 最後のパーティ
        args[x].server = 1;
        args[x].port = _Parties[_party]->port + (i*num_parties + num_parties-1);
        params[x] = thread_new(comm_init_thread, &args[x]);
        //printf("e i=%d x=%d port %d\n", i, x, args[x].port);
      }
      if (_party != 1) {
        int x = i*num_parties + _party-1; // 一つ前に接続
        args[x].server = 0;
        args[x].dest_name = _Parties[_party-1]->addr;
        args[x].port = _Parties[_party-1]->port + (i*num_parties + _party);
        params[x] = thread_new(comm_init_thread, &args[x]);
        //printf("f i=%d x=%d server %s port %d\n", i, x, args[x].dest_name, args[x].port);
      }
      if (_party == num_parties-1 && num_parties > 3) {
        int x = i*num_parties + 1; // P1 に接続
        args[x].server = 0;
        args[x].dest_name = _Parties[1]->addr;
        //printf("xxx %d\n", (i*num_parties + _party));
        args[x].port = _Parties[1]->port + (i*num_parties + _party);
        params[x] = thread_new(comm_init_thread, &args[x]);
        //printf("g i=%d x=%d server %s port %d\n", i, x, args[x].dest_name, args[x].port);
      }
    }
  }

  if (_party == 0) {
    for (int j=1; j<num_parties; j++) {
      for (int i=0; i<num_channels; i++) {
        int x = i*num_parties+j;
        thread_end(params[x]);
        _C[x] = args[x].ans;
        _C[x]->total_send = 0;
        _C[x]->total_recv = 0;
        _C[x]->total_send_rounds = 0;
        _C[x]->total_recv_rounds = 0;
      }
    }
  } else {
    for (int i=0; i<num_channels; i++) {
      int x = i*num_parties+TO_SERVER;
      thread_end(params[x]);
      _C[x] = args[x].ans;
      _C[x]->total_send = 0;
      _C[x]->total_recv = 0;
      _C[x]->total_send_rounds = 0;
      _C[x]->total_recv_rounds = 0;
      if (_party != num_parties-1) {
        int x = i*num_parties + _party+1;
        thread_end(params[x]);
        _C[x] = args[x].ans;
        _C[x]->total_send = 0;
        _C[x]->total_recv = 0;
        _C[x]->total_send_rounds = 0;
        _C[x]->total_recv_rounds = 0;
      }
      if (_party == 1 && num_parties > 3) {
        int x = i*num_parties + num_parties-1;
        thread_end(params[x]);
        _C[x] = args[x].ans;
        _C[x]->total_send = 0;
        _C[x]->total_recv = 0;
        _C[x]->total_send_rounds = 0;
        _C[x]->total_recv_rounds = 0;
      }
      if (_party != 1) {
        int x = i*num_parties + _party-1; // 一つ前に接続
        thread_end(params[x]);
        _C[x] = args[x].ans;
        _C[x]->total_send = 0;
        _C[x]->total_recv = 0;
        _C[x]->total_send_rounds = 0;
        _C[x]->total_recv_rounds = 0;
      }
      if (_party == num_parties-1 && num_parties > 3) {
        int x = i*num_parties + 1;
        thread_end(params[x]);
        _C[x] = args[x].ans;
        _C[x]->total_send = 0;
        _C[x]->total_recv = 0;
        _C[x]->total_send_rounds = 0;
        _C[x]->total_recv_rounds = 0;
      }
    }
  }

  NEWA(_send_queue_idx, int, num_parties * num_channels);
  NEWA(_send_queue, char*, num_parties * num_channels);
  for (int i = 0; i < num_parties * num_channels; ++i) {
    _send_queue_idx[i] = 0;
    NEWA(_send_queue[i], char, BUFFER_SIZE);
  }

  free(params);
  free(args);

  PRG_initialize(_opt.parties);
}

long get_total_send(void)
{
  long total_send = 0;
  if (_C == 0) return total_send;

  for (int i=0; i<_opt.channels*_opt.parties; i++) {
    if (_C[i] != NULL) {
      total_send += _C[i]->total_send;
    }
  }
  return total_send;
}

long get_total_recv(void)
{
  long total_recv = 0;
  if (_C == 0) return total_recv;

  for (int i=0; i<_opt.channels*_opt.parties; i++) {
    if (_C[i] != NULL) {
      total_recv += _C[i]->total_recv;
    }
  }
  return total_recv;
}

static void mpc_end()
{
  PRG_free();
  precomp_tables_free();
  if (_party < 0) {
    party_free(_Parties, _opt.parties);
    return;
  }
  long total_send = 0;
  long total_recv = 0;
  long total_send_rounds = 0;
  long total_recv_rounds = 0;

  for (int i=0; i<_opt.channels*_opt.parties; i++) {
    if (_C[i] != NULL) {
      total_send += _C[i]->total_send;
      total_recv += _C[i]->total_recv;
      total_send_rounds += _C[i]->total_send_rounds;
      total_recv_rounds += _C[i]->total_recv_rounds;
      comm_close(_C[i]);
    }
  }
  printf("total send %ld bytes\n", total_send);
  printf("total recv %ld bytes\n", total_recv);
  printf("total send rounds %ld\n", total_send_rounds);
  printf("total recv rounds %ld\n", total_recv_rounds);

  for (int i = 0; i < _opt.parties * _opt.channels; ++i) {
    free(_send_queue[i]);
  }
  free(_send_queue_idx);
  free(_send_queue);

  party_free(_Parties, _opt.parties);
  free(_C);
}

int _comm_flag = 0;


static void mpc_send_channel(int party_to, void *buf, int size, int channel)
{
  //if (channel == 0 && _comm_flag > 0) {
  //  printf("break\n");
  //}
  if (party_to >= _opt.parties * _opt.channels) {
    printf("mpc_send: party_to %d NP %d\n", party_to, _opt.parties);
    exit(1);
  }
  if (_party < 0) return;

//  if (send_queue_idx[party_to]>0) mpc_send_flush(party_to);

  comm c = _C[channel*_num_parties+party_to];

  int s = 0;
  //printf("mpc_send %d bytes to party %d\n", size, party_to);
  while (s < size) {
    s += comm_send_block(c, buf+s, size-s);
  //  sleep(0.01);
  }
  c->total_send += size;
  c->total_send_rounds += 1;  // comm_send_blockを呼び出した回数にした方が良い？？
//  if (_party == 0) printf("total %ld        \r", c->total_send);
}
#define mpc_send(party_to, buf, size) mpc_send_channel(party_to, buf, size, 0)

static void mpc_send_flush_channel(int party_to, int channel)
{
  //mpc_send(channel*_num_parties+party_to, _send_queue[channel*_num_parties+party_to], _send_queue_idx[channel*_num_parties+party_to]);
  mpc_send_channel(party_to, _send_queue[channel*_num_parties+party_to], _send_queue_idx[channel*_num_parties+party_to], channel);
  _send_queue_idx[channel*_num_parties+party_to] = 0;
}
#define mpc_send_flush(party_to) mpc_send_flush_channel(party_to, 0)

static void mpc_send_queue_channel(int party_to, void *buf, int size, int channel)
{
  if (_send_queue_idx[channel*_num_parties+party_to] + size > BUFFER_SIZE) {
    mpc_send_flush(channel*_num_parties+party_to);
    mpc_send_channel(party_to, buf, size, channel);
    return;
  }
  int p = _send_queue_idx[channel*_num_parties+party_to];
  char *b = (char *)buf;
  for (int i=0; i<size; i++) {
    _send_queue[channel*_num_parties+party_to][p+i] = b[i];
  }
  _send_queue_idx[channel*_num_parties+party_to] += size;
}
#define mpc_send_queue(party_to, buf, size) mpc_send_queue_cannel(party_to, buf, size, 0)

static void mpc_recv_channel(int party_from, void *buf, int size, int channel)
{
  if (party_from >= _opt.parties * _opt.channels) {
    printf("mpc_recv: party_from %d NP %d\n", party_from, _opt.parties);
    exit(1);
  }
  if (_party < 0) return;
  comm c = _C[channel*_num_parties+party_from];
  int r = 0;
  //printf("mpc_recv %d bytes from party %d\n", size, party_from);
  while (r < size) {
    r += comm_recv_block(c, buf+r, size-r);
  //  sleep(0.01);
  }
  c->total_recv += size;
  c->total_recv_rounds += 1;  // comm_recv_blockを呼び出した回数にした方が良い？？
}
#define mpc_recv(party_from, buf, size) mpc_recv_channel(party_from, buf, size, 0)


static void mpc_exchange_channel(void *buf_send, void *buf_recv, int size, int channel)
{
//  if (channel == 0 && _comm_flag > 0) {
//    printf("break\n");
//  }
  if (_party <= 0) return;
  comm c = _C[_num_parties*channel+TO_PAIR];
  int r = 0, s = 0;
  while (r < size || s < size) {
    if (r < size) r += comm_recv_block(c, buf_recv+r, size-r);
    if (s < size) s += comm_send_block(c, buf_send+s, size-s);
  //  sleep(0.01);
  }
  c->total_send += size;
  c->total_recv += size;
  c->total_send_rounds += 1;
  c->total_recv_rounds += 1;
}
#define mpc_exchange(buf_send, buf_recv, size) mpc_exchange_channel(buf_send, buf_recv, size, 0)





#undef NP


#endif
