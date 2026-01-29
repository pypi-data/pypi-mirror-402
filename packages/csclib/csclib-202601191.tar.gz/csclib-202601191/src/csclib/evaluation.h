#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/stat.h>

#include "share.h"

#ifndef NP
#define NP (NC*2+1)

FILE* OpenFile(char *file_name, char *mode) {
    FILE *fp = fopen(file_name, mode);
    if (fp == NULL) {
        printf("cannot open %s.\n", file_name);
        exit(1);
    }
    return fp;
}

// dnameで指定されるパスのディレクトリが存在するなら0を返す
// 存在しないならそのディレクトリを作成し，１を返す．
int MakeDir(char *dname) {
    struct stat statBuf;
    if (stat(dname, &statBuf) == 0) {
        return 0;
    }
    else {
        mkdir(dname, 0775);
        return 1;
    }
}

// その時点までに記録された通信量，通信ラウンドをリセットする．
// この関数を呼び出した場合，mpc_end()による通信量の計算の値には意味がなくなることに注意．
void ResetMpcStat() {
#if 0
    for (int i = 1; i < _opt.parties; i += 2) {
        _C[i]->total_send = 0;
        _C[i]->total_recv = 0;
        _C[i+1]->total_send = 0;
        _C[i+1]->total_recv = 0;

        _C[i]->total_send_rounds = 0;
        _C[i]->total_recv_rounds = 0;
        _C[i+1]->total_send_rounds = 0;
        _C[i+1]->total_recv_rounds = 0;
    }
#else
    for (int i = 0; i < _opt.channels*_opt.parties; i ++) {
        if (_C[i] != NULL) {
          _C[i]->total_send = 0;
          _C[i]->total_recv = 0;
          _C[i]->total_send_rounds = 0;
          _C[i]->total_recv_rounds = 0;
        }
    }
#endif
}

// 実行時に記録すべき項目をまとめた構造体
typedef struct {
    double exe_time;
    long total_send1;
    long total_send2;
    long total_recv1;
    long total_recv2;
    int total_send_round1;
    int total_send_round2;
    int total_recv_round1;
    int total_recv_round2;
}* MpcExeData;

// 現時点の通信に関する各種データを計算する．
MpcExeData GetCurrentMpcExeData() {
    NEWT(MpcExeData, data);
    data->exe_time = time(NULL);
    data->total_send1 = data->total_send2 = data->total_recv1 = data->total_recv2 = 0;
    data->total_send_round1 = data->total_send_round2 = data->total_recv_round1 = data->total_recv_round2 = 0;
#if 0
    for (int i = 1; i < _opt.channels*_opt.parties; i += 2) {
      if (_C[i] != NULL) {
        data->total_send1 += _C[i]->total_send;
        data->total_recv1 += _C[i]->total_recv;
        data->total_send2 += _C[i+1]->total_send;
        data->total_recv2 += _C[i+1]->total_recv;
        
        data->total_send_round1 += _C[i]->total_send_rounds;
        data->total_recv_round1 += _C[i]->total_recv_rounds;
        data->total_send_round2 += _C[i+1]->total_send_rounds;
        data->total_recv_round2 += _C[i+1]->total_recv_rounds;
      }
    }
#else
    for (int i = 0; i < _opt.channels; i++) {
      comm c;
      if (_party == 0) {
        c = _C[i*_opt.parties+ TO_PARTY1];
        if (c != NULL) {
          data->total_send1 += c->total_send;
          data->total_recv1 += c->total_recv;
          data->total_send_round1 += c->total_send_rounds;
          data->total_recv_round1 += c->total_recv_rounds;
        }
        c = _C[i*_opt.parties+ TO_PARTY2];
        if (c != NULL) {
          data->total_send2 += c->total_send;
          data->total_recv2 += c->total_recv;
          data->total_send_round2 += c->total_send_rounds;
          data->total_recv_round2 += c->total_recv_rounds;
        }
      } else {
        c = _C[i*_opt.parties+ TO_SERVER];
        if (c != NULL) {
          data->total_send1 += c->total_send;
          data->total_recv1 += c->total_recv;
          data->total_send_round1 += c->total_send_rounds;
          data->total_recv_round1 += c->total_recv_rounds;
        }
        c = _C[i*_opt.parties+ TO_PAIR];
        if (c != NULL) {
          data->total_send2 += c->total_send;
          data->total_recv2 += c->total_recv;
          data->total_send_round2 += c->total_send_rounds;
          data->total_recv_round2 += c->total_recv_rounds;
        }
      }
    }
#endif
    return data;
}

MpcExeData GetDataDiff(MpcExeData start_data, MpcExeData end_data) {
    NEWT(MpcExeData, data_diff);
    data_diff->exe_time = difftime(end_data->exe_time, start_data->exe_time);
    data_diff->total_send1 = end_data->total_send1 - start_data->total_send1;
    data_diff->total_send2 = end_data->total_send2 - start_data->total_send2;
    data_diff->total_recv1 = end_data->total_recv1 - start_data->total_recv1;
    data_diff->total_recv2 = end_data->total_recv2 - start_data->total_recv2;
    data_diff->total_send_round1 = end_data->total_send_round1 - start_data->total_send_round1;
    data_diff->total_send_round2 = end_data->total_send_round2 - start_data->total_send_round2;
    data_diff->total_recv_round1 = end_data->total_recv_round1 - start_data->total_recv_round1;
    data_diff->total_recv_round2 = end_data->total_recv_round2 - start_data->total_recv_round2;

    return data_diff;
}

void fprintMpcExeData(FILE *fp, MpcExeData data) {
    fprintf(fp, "execution time %f\n", data->exe_time);
    fprintf(fp, "total send %ld + %ld\n", data->total_send1, data->total_send2);
    fprintf(fp, "total recv %ld + %ld\n", data->total_recv1, data->total_recv2);
    fprintf(fp, "total send rounds %d + %d\n", data->total_send_round1, data->total_send_round2);
    fprintf(fp, "total recv rounds %d + %d\n", data->total_recv_round1, data->total_recv_round2);
    fflush(fp);
}

#endif