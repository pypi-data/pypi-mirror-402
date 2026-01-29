////////////////////////////////////////////////////////
// 通信に関する処理
////////////////////////////////////////////////////////


#ifndef _COMM_H
 #define _COMM_H

#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

#if !defined(SOL_TCP) && defined(IPPROTO_TCP)
#define SOL_TCP IPPROTO_TCP
#endif

//#ifndef NEW
// #define NEW(p,n) {p = malloc((n)*sizeof(*p));if ((p)==NULL) {printf("not enough memory\n"); exit(1);};}
//#endif

#ifndef NEWA
 #define NEWA(p,t,n) {p = (t*)malloc((n)*sizeof(*p));if ((p)==NULL) {printf("not enough memory\n"); exit(1);};}
#endif

#ifndef NEWT
 #define NEWT(t, p) \
  t p; \
  p = (t)malloc(sizeof(*p)); \
  if ((p)==NULL) {printf("not enough memory\n"); exit(1);}
#endif

typedef struct {
  int Socket;
// 相手のアドレス
  char *dstname;
  struct sockaddr_in dstAddr;
  int dstport;

// 自分のアドレス
//  char *srcname;
  struct sockaddr_in srcAddr;
  int srcport;

  long total_send, total_recv;
  long total_send_rounds, total_recv_rounds;

}* comm;

//#define BUFFER_SIZE 256 // これは遅い
//#define BUFFER_SIZE (1<<12)
#define BUFFER_SIZE (1<<16)
//#define BUFFER_SIZE (1<<20)


static comm comm_init_server(int recv_port)
{
//  comm C;
  NEWT(comm, C);
  int sock;
  int ret;
  C->dstname = NULL;
////////////////////////////////////////////////////////////
// サーバー側の設定
////////////////////////////////////////////////////////////
  memset(&C->srcAddr, 0, sizeof(C->srcAddr));
  C->srcAddr.sin_family = AF_INET;
  C->srcAddr.sin_port = htons(recv_port);
  C->srcAddr.sin_addr.s_addr = INADDR_ANY;
  C->srcport = recv_port;

  //printf("socket port %d\n", recv_port);
//  getchar();

  /* ソケットの生成 */
  if((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    perror("socket");
    free(C);
    return NULL;
  }
  //printf("socket %d\n", sock);

  int opt = 1;
//  int opt = SO_REUSEADDR | SO_LINGER;
  if (_opt.comm_no_delay) {
    printf("NODELAY\n");
    if (setsockopt(sock, SOL_TCP, TCP_NODELAY, (const char *)&opt, sizeof(opt)) < 0) {
      perror("setsockopt");
      exit(1);
    }
  } else {
    printf("REUSEADDR\n");
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, (const char *)&opt, sizeof(opt)) < 0) {
      perror("setsockopt");
      exit(1);
    }
  }

  //printf("bind\n");
//  getchar();

  /* ソケットのバインド */
  if (bind(sock, (struct sockaddr *) &C->srcAddr, sizeof(C->srcAddr)) < 0) {
    perror("bind");
    free(C);
    exit(1);
    return NULL;
  }

  //printf("listen\n");
//  getchar();
  /* 接続の許可 */
  if (listen(sock, 3) < 0) {
    perror("listen:");
  }

  unsigned int dstAddrSize = sizeof(struct sockaddr_in);
  while (1) {
    //printf("do accept\n");
    ret = accept(sock, (struct sockaddr *) &C->dstAddr, &dstAddrSize);
    if (ret != -1) {
      C->Socket = ret;
      //printf("Connected from %s %d\n", inet_ntoa(C->dstAddr.sin_addr), recv_port);
      break;
    } else {
      perror("accept");
    }
    sleep(1);
  }
  close(sock);

  //printf("done\n");
  return C;
}

static comm comm_init_client(char *dest_name, int dest_port)
{
//  comm C;
  NEWT(comm, C);
  C->dstname = strdup(dest_name);

////////////////////////////////////////////////////////////
// クライアント側の設定
////////////////////////////////////////////////////////////
  while (1) {
  /* sockaddr_in 構造体のセット */
    memset(&C->dstAddr, 0, sizeof(C->dstAddr));
    C->dstAddr.sin_port = htons(dest_port);
    C->dstAddr.sin_family = AF_INET;
    C->dstAddr.sin_addr.s_addr = inet_addr(dest_name);

  //printf("socket\n");
  /* ソケット生成 */
    if ((C->Socket = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
      perror("socket");
      free(C->dstname);
      free(C);
      return NULL;
    }
    //printf("dstSocket %d %s:%d\n", C->Socket, dest_name, dest_port);

////////////////////////////////////////////////////////////
// 接続
////////////////////////////////////////////////////////////

    //printf("client: Trying to connect to %s:%d \n", dest_name, dest_port);
    int ret = connect(C->Socket, (struct sockaddr *) &C->dstAddr, sizeof(C->dstAddr));
    if (ret == 0) { // 相手が listen するまで connect できない
      //printf("connected to %s:%d \n", dest_name, dest_port);
      break;
    }
    if (ret < 0) {
      //perror("connect");
    }
    close(C->Socket);
    sleep(1);
  }
  //printf("done\n");
  return C;
}

static void comm_close(comm C)
{
  if (C == NULL) return;
  if (C->dstname != NULL) { // client
    //if (shutdown(C->Socket, SHUT_RDWR)) perror("shutdown ");
    if (shutdown(C->Socket, SHUT_WR)) perror("shutdown ");
  } else { // server
    char buf[1];
    ssize_t size = 1;
    while (size > 0) {
      size = recv(C->Socket, buf, size, 0);
      if (size > 0) {
        printf("??? recv %d\n", (int)buf[0]);
      }
    }
  }
  close(C->Socket);
//  if (closesocket(C->Socket)) perror("closesocket ");
  if (C->dstname != NULL) free(C->dstname);
  free(C);
}

static void comm_send(comm C, char *buf, int len)
{
  ssize_t size;
  size = send(C->Socket, buf, len, 0);
  if (size < 0) {
    perror("comm_send:send");
  }
  if (size < len) {
    printf("comm_send: sent %ld < %d\n", size, len);
  }
}

static void comm_recv(comm C, char *buf, int len)
{
  ssize_t size;
  size = recv(C->Socket, buf, len, 0);
  if (size < 0) {
    perror("comm_recv:recv");
  }
  if (size < len) {
    printf("comm_recv: received %ld < %d\n", size, len);
  }
}

static int comm_recv_block(comm C, char *buffer, int len)
{
  fd_set rfds;
  struct timeval tv;
  int retval;
  int b;

  FD_ZERO(&rfds);

  tv.tv_sec = 0;
  tv.tv_usec = 500;

  b = 0;
  FD_SET(C->Socket, &rfds);
  retval = select(FD_SETSIZE, &rfds, NULL, NULL, &tv);
  if (retval < 0) {
    perror("select()");
  } else if(retval > 0) {
    if (FD_ISSET(C->Socket,&rfds)) {
      FD_CLR(C->Socket, &rfds);
      if (len > BUFFER_SIZE) len = BUFFER_SIZE;
      b = recv(C->Socket, buffer, len, 0); 
      if (b == -1) {
        perror("recv");
        printf("??? b %d\n", b);
      }
    }
  }
  //if (b > 0) printf("recv %d\n", b);
  return b;
}

static int comm_send_block(comm C, char *buf, int len)
{
//  int size = len;
  if (len > BUFFER_SIZE) len = BUFFER_SIZE;
  send(C->Socket, buf, len, 0);
  return len;
}


#endif
