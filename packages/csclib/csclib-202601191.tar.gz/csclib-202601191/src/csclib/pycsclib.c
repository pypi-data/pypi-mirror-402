// https://cpp-learning.com/python_c_api_step1/

#define PY_SSIZE_T_CLEAN
//#include <python3.10/Python.h>
//#include <python3.10/structmember.h>
#include <Python.h>
#include <structmember.h>

#include "share.h"
//#include "../../share.h"

/*********************************************
# setup.py
from distutils.core import setup, Extension

setup(name = 'csclib', version = '0.0.1',  \
   ext_modules = [Extension('csclib', ['pytest.c'])])
*********************************************/

typedef struct {
  PyObject_HEAD
  share_array a;
} CsclibObject;

typedef struct {
  PyObject_HEAD
  _bits a;
} CsclibBObject;

static PyTypeObject CsclibType;
static PyTypeObject CsclibBType;

static PyModuleDef csclibmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "csclib",
    .m_doc = "csclib module.",
    .m_size = -1,
};


static void
Csclib_dealloc(CsclibObject *self)
{
//  printf("dealloc\n");
//  if (self->a) _print(self->a);
  if (self->a) _free(self->a);
  Py_TYPE(self)->tp_free((PyObject *) self);
}

static void
Csclib_Bdealloc(CsclibBObject *self)
{
//  printf("dealloc\n");
//  if (self->a) _print(self->a);
  if (self->a) _free_bits(self->a);
  Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
Csclib_start(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  int i;
  printf("Csclib_start\n");

  _party = -1;

  if (PyArg_ParseTuple(args, "i", &i)){
    _party = i;
  }


  printf("initialize party = %d\n", _party);
//  mpc_start(3);
//  PRG_initialize();
  mpc_start();

  Py_RETURN_NONE;
}


static int
Csclib_init(CsclibObject *self, PyObject *args, PyObject *kwds)
{
//  int i;
//  printf("init %p %p %p\n", self, args, kwds);
  return 0;
}

static int
Csclib_Binit(CsclibBObject *self, PyObject *args, PyObject *kwds)
{
//  int i;
//  printf("init %p %p %p\n", self, args, kwds);
  return 0;
}

static PyObject* Csclib_array(PyObject* self, PyObject* args)
{
  int n, q;
  PyObject *c_list, *item;
  share_t *A;

//  printf("array rec count %d\n", Py_REFCNT(self));


  if (_party <= 0 || 1) {
    if (!PyArg_ParseTuple(args, "Oi", &c_list, &q)){
        printf("array\n");
        return NULL;
    }
    if (PyList_Check(c_list)) {
      n = PyList_Size(c_list);
    } else {
      return NULL;
    }
  }
  //printf("n %d q %d\n", n, q);
  NEWA(A, share_t, n);

  if (_party <= 0 || 1) {
    for (int i = 0; i < n; i++){
      item = PyList_GetItem(c_list, i);
      share_t x = PyLong_AsLong(item);
      x = MOD(x); // 入力が範囲外のときはエラー処理をするほうが良い？
      A[i] = x;
      //Py_DECREF(item); // !!! これ不要
    }
  }

  _ ans = share_new(n, q, A);
  free(A);

  CsclibObject *p = (CsclibObject*)self;
  if (p->a != NULL) {
    printf("array free ");
  //  _print(p->a);
    _free(p->a);
  }
  p->a = ans;
//  Py_INCREF(self); // 必要
//  return self;
  return Py_BuildValue("O", self);
}


static PyObject* Csclib_const(PyObject* self, PyObject* args)
{
  int n, v, q;
  if (!PyArg_ParseTuple(args, "iii", &n, &v, &q)){
      printf("const\n");
      return NULL;
  }
//  printf("n %d v %d q %d\n", n, v, q);
  _ ans = share_const(n, v, q);
//  printf("const %p\n", ans);
//  _print(ans);
  CsclibObject *p = (CsclibObject*)self;
  if (p->a != NULL) {
    printf("array free ");
  //  _print(p->a);
    _free(p->a); // 元々何か入っていたら解放
  }
  p->a = ans;
//  Py_INCREF(self); // 必要
//  return self;
  return Py_BuildValue("O", self);
}

static PyObject* Csclib_get(CsclibObject* self, PyObject *Py_UNUSED(ignored))
{
  _ p = self->a;
  if (p != NULL) {
    PyObject* c_list = PyList_New(p->n);
    for (int i=0; i<p->n; i++) {
      PyList_SET_ITEM(c_list, i, PyLong_FromLong(pa_get(p->A, i)));
    }
    return Py_BuildValue("O", c_list);
  } else {
    Py_RETURN_NONE;
  }
}

/////////////////////////////////////////////////////////////////
// シェアに生の配列を入れる．シェアのメモリは事前に確保しておく．
/////////////////////////////////////////////////////////////////
static PyObject* Csclib_set(CsclibObject* self, PyObject* args)
{
  PyObject *c_list, *item;
  int n;
  share_t q;

  if (!PyArg_ParseTuple(args, "O", &c_list)){
    printf("set\n");
    return NULL;
  }
  if (PyList_Check(c_list)) {
    n = PyList_Size(c_list);
  } else {
    return NULL;
  }
  _ p = self->a;
  if (p->n != n) {
    printf("set: p->n = %d n = %d\n", p->n, n);
    return NULL;
  }
  q = p->q;
  if (_party <= 0 || 1) {
    for (int i = 0; i < n; i++){
      item = PyList_GetItem(c_list, i);
      share_t x = PyLong_AsLong(item);
      x = MOD(x); // 入力が範囲外のときはエラー処理をするほうが良い？
      pa_set(p->A, i, x);
    }
  }
  return Py_BuildValue("O", self);
  Py_RETURN_NONE;
}

#define FUNC_NEWSHARE(func) \
static PyObject* Csclib_ ## func(PyObject* self, PyObject *Py_UNUSED(ignored)) \
{ \
  _ p = ((CsclibObject*)self)->a; \
  if (p != NULL) { \
    _ ans = func(p); \
    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0); \
    new_obj->a = ans; \
    return (PyObject*)new_obj; \
  } else { \
    Py_RETURN_NONE; \
  } \
}




static PyObject* Csclib_print(CsclibObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("print rec count %d\n", Py_REFCNT(self));
  _ p = self->a;
  if (p != NULL) _print(p);
//  Py_INCREF(self);
//  return self;
//  return Py_BuildValue("O", self);
  Py_RETURN_NONE;
}

static PyObject* Csclib_len(CsclibObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("len rec count %d\n", Py_REFCNT(self));
  _ p = self->a;
  if (p != NULL) {
  //  Py_INCREF(self); // test
    return Py_BuildValue("i", p->n);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_order(CsclibObject* self, PyObject *Py_UNUSED(ignored))
{
  _ p = self->a;
  if (p != NULL) {
  //  Py_INCREF(self); // test
    return Py_BuildValue("i", p->q);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_check(CsclibObject* self, PyObject *Py_UNUSED(ignored))
{
  printf("check rec count %d\n", (int)Py_REFCNT(self));
  _ p = self->a;
  if (p != NULL) {
    _check(p);
  //  Py_INCREF(self);
  //  return self;
  //  return Py_BuildValue("O", self);
    Py_RETURN_NONE;
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_reconstruct(PyObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("reconstruct rec count %d\n", Py_REFCNT(self));
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = _reconstruct(p);
  //  printf("reconstruct ");
  //  _print(ans);
  //  Py_INCREF(self);  // test

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

#if 0
static PyObject* Csclib_PrefixSum(PyObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("reconstruct rec count %d\n", Py_REFCNT(self));
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = PrefixSum(p);
  //  printf("reconstruct ");
  //  _print(ans);
  //  Py_INCREF(self);  // test

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}
#else
FUNC_NEWSHARE(PrefixSum)
#endif

#if 0
static PyObject* Csclib_SuffixSum(PyObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("reconstruct rec count %d\n", Py_REFCNT(self));
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = SuffixSum(p);
  //  printf("reconstruct ");
  //  _print(ans);
  //  Py_INCREF(self);  // test

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_rank0(PyObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("reconstruct rec count %d\n", Py_REFCNT(self));
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = rank0(p);
  //  printf("reconstruct ");
  //  _print(ans);
  //  Py_INCREF(self);  // test

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_rank1(PyObject* self, PyObject *Py_UNUSED(ignored))
{
//  printf("reconstruct rec count %d\n", Py_REFCNT(self));
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = rank1(p);
  //  printf("reconstruct ");
  //  _print(ans);
  //  Py_INCREF(self);  // test

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_dup(PyObject* self, PyObject *Py_UNUSED(ignored))
{
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _ ans = _dup(p);
  //  printf("dup ");
  //  _print(ans);

  //  Py_INCREF(self); // test
    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    if (new_obj == NULL) {
      printf("dup null?\n");
    }
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
    printf("dup?\n");
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

#else
FUNC_NEWSHARE(SuffixSum)
FUNC_NEWSHARE(rank0)
FUNC_NEWSHARE(rank1)
FUNC_NEWSHARE(select0)
FUNC_NEWSHARE(select1)
FUNC_NEWSHARE(sum)
FUNC_NEWSHARE(_dup)
FUNC_NEWSHARE(StableSort)
#define Csclib_dup Csclib__dup
#endif

static PyObject* Csclib_randomize(PyObject* self, PyObject *Py_UNUSED(ignored))
{
  _ p = ((CsclibObject*)self)->a;
  if (p != NULL) {
    _randomize(p);
  //  Py_INCREF(self);
  //  return self;
    Py_RETURN_NONE;
  } else {
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_dup_bits(PyObject* self, PyObject *Py_UNUSED(ignored))
{
  _bits p = ((CsclibBObject*)self)->a;
  if (p != NULL) {
    _bits ans = _dup_bits(p);
  //  printf("dup ");
  //  _print(ans);

  //  Py_INCREF(self); // test
    CsclibBObject *new_obj = (CsclibBObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    if (new_obj == NULL) {
      printf("dup_bits null?\n");
    }
    new_obj->a = ans;
    return (PyObject*)new_obj;
//    return Py_BuildValue("O", new_obj);
  } else {
    printf("dup_bits?\n");
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

///////////////////////////////////////////////////////////////////
// シェアを self のクラスにコピーする
// (self が継承したクラスの場合に使う
///////////////////////////////////////////////////////////////////
static PyObject* Csclib_copy(PyObject* self, PyObject* args)
{
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("copy\n");
    return NULL;
  }
  _ q = ((CsclibObject*)p)->a;
  if (q != NULL) {
    _ ans = _dup(q);

    CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    if (new_obj == NULL) {
      printf("copy null?\n");
    }
    new_obj->a = ans;
    return (PyObject*)new_obj;
  } else {
    printf("copy?\n");
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}


static PyObject* Csclib_setpublic(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    printf("setpublic\n");
    return NULL;
  }
//  printf("setpublic i=%d x=%d\n", i, x);
  _ a = ((CsclibObject*)self)->a;
  _setpublic(a, i, x);
//  _print(a);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}

static PyObject* Csclib_setshare(PyObject* self, PyObject* args)
{
  int i, j;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("setshare\n");
    return NULL;
  }
//  printf("setshare i=%d j=%d\n", i, j);

  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _setshare(a, i, b, j);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}

#if 0
static PyObject* Csclib_getone(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "i", &i)){
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  x = share_getone(a, i);
//  Py_INCREF(self); // test
  return Py_BuildValue("i", x);
}

static PyObject* Csclib_setone(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    printf("setone\n");
    return NULL;
  }
//  printf("setone\n");
  _ a = ((CsclibObject*)self)->a;
  share_setone(a, i, x);
//  Py_INCREF(self); // 必要
//  return self;
//  Py_INCREF(self);
  Py_RETURN_NONE;
}

static PyObject* Csclib_public0(PyObject* self, PyObject* args)
{
  int x;
  if (!PyArg_ParseTuple(args, "i", &x)){
    printf("public\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  share_t q = a->q;
  if (_party != 2) {
    x = MOD(x);
  } else {
    x = 0;
  }
//  Py_INCREF(self); // test
  return Py_BuildValue("i", x);
}
#endif

static PyObject* Csclib_public(PyObject* self, PyObject* args)
{
  int x;
  if (!PyArg_ParseTuple(args, "i", &x)){
    printf("public\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  share_t q = a->q;

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = _const(1, x, q);
  return (PyObject*)new_obj;
}

static PyObject* Csclib_setshares(PyObject* self, PyObject* args)
{
  int is, ie, js;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iiOi", &is, &ie, &p, &js)){
    printf("setshares\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _setshares(a, is, ie, b, js);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}

// 自分を書き換える
#if 0
static PyObject* Csclib_addpublic0(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _addpublic(a, i, x);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}
#endif

// コピーして書き換える
static PyObject* Csclib_addpublic(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    return NULL;
  }
  PyObject* new_obj = Csclib__dup(self, NULL);

  _ a = ((CsclibObject*)new_obj)->a;
//  printf("Csclib_addpublic i=%d x=%d\n", i, x);
//  _print(a);
  _addpublic(a, i, x);
  return new_obj;
}

static PyObject* Csclib_subpublic(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    return NULL;
  }
  PyObject* new_obj = Csclib__dup(self, NULL);

  _ a = ((CsclibObject*)new_obj)->a;
  _subpublic(a, i, x);
  return new_obj;
}

#if 0
static PyObject* Csclib_addshare0(PyObject* self, PyObject* args)
{
  int i, j;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("addshare\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _addshare(a, i, b, j);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}
#endif

static PyObject* Csclib_addshare(PyObject* self, PyObject* args)
{
  int i, j;
  printf("Csclib_addshare\n");
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("addshare\n");
    return NULL;
  }
  PyObject* new_obj = Csclib__dup(self, NULL);

  _ a = ((CsclibObject*)new_obj)->a;
  _ b = ((CsclibObject*)p)->a;
  _addshare(a, i, b, j);
  return new_obj;
}

#if 0
static PyObject* Csclib_subshare0(PyObject* self, PyObject* args)
{
  int i, j;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("subshare\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _subshare(a, i, b, j);
//  Py_INCREF(self);
//  return self;
  Py_RETURN_NONE;
}
#endif

static PyObject* Csclib_subshare(PyObject* self, PyObject* args)
{
  int i, j;
  printf("Csclib_subshare\n");
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("subshare\n");
    return NULL;
  }
  PyObject* new_obj = Csclib_dup(self, NULL);

  _ a = ((CsclibObject*)new_obj)->a;
  _ b = ((CsclibObject*)p)->a;
  _subshare(a, i, b, j);
  return new_obj;
}

static PyObject* Csclib_mulpublic(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    printf("mulpublic\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _mulpublic(a, i, x);
//  Py_INCREF(self); // 必要
//  return self;
  Py_RETURN_NONE;
}

static PyObject* Csclib_slice(PyObject* self, PyObject* args)
{
  int start, end;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "ii", &start, &end)){
    printf("slice\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = _slice(a, start, end);
//  printf("slice ");
//  _print(ans);
//  Py_INCREF(self); // test
  
  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
//  return new_obj;
//  return Py_BuildValue("O", new_obj);
  return (PyObject*)new_obj;
}

#define FUNC_NEWSHARE_O(func) \
static PyObject* Csclib_ ## func(PyObject* self, PyObject* args) \
{ \
  PyObject* arg1; \
  if (!PyArg_ParseTuple(args, "O", &arg1)){ \
    return NULL; \
  } \
  _ a = ((CsclibObject*)self)->a; \
  _ b = ((CsclibObject*)arg1)->a; \
  _ ans = func(a, b); \
  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0); \
  new_obj->a = ans; \
  return (PyObject*)new_obj; \
}

#define FUNC_NEWSHARE_i(func) \
static PyObject* Csclib_ ## func(PyObject* self, PyObject* args) \
{ \
  int arg1; \
  if (!PyArg_ParseTuple(args, "i", &arg1)){ \
    return NULL; \
  } \
  _ a = ((CsclibObject*)self)->a; \
  _ ans = func(a, arg1); \
  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0); \
  new_obj->a = ans; \
  return (PyObject*)new_obj; \
}

#define FUNC_O(func) \
static PyObject* Csclib_ ## func(PyObject* self, PyObject* args) \
{ \
  PyObject* arg1; \
  if (!PyArg_ParseTuple(args, "O", &arg1)){ \
    return NULL; \
  } \
  _ a = ((CsclibObject*)self)->a; \
  _ b = ((CsclibObject*)arg1)->a; \
  func(a, b); \
  Py_RETURN_NONE; \
}

#define FUNC_(func) \
static PyObject* Csclib_ ## func(PyObject* self, PyObject* *Py_UNUSED(ignored)) \
{ \
  _ a = ((CsclibObject*)self)->a; \
  func(a); \
  Py_RETURN_NONE; \
}


#if 0
static PyObject* Csclib__concat(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("concat\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = _concat(a, b);
//  printf("concat ");
//  _print(ans);
//  Py_INCREF(self); // test
  
  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}
#else
FUNC_NEWSHARE_O(_concat)
#endif

FUNC_NEWSHARE_i(Diff)
FUNC_O(addall)
FUNC_(setperm)

static PyObject* Csclib_insert_head(PyObject* self, PyObject* args)
{
  int x;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &x)){
    printf("insert_head\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = _insert_head(a, x);
//  Py_INCREF(self); // test
  
  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_insert_tail(PyObject* self, PyObject* args)
{
  int x;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &x)){
    printf("insert_tail\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = _insert_tail(a, x);
//  Py_INCREF(self); // test
  
  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_vadd(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vadd\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = vadd(a, b);
//  Py_INCREF(self); // test
  
  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_vsub(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vsub\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = vsub(a, b);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}


static PyObject* Csclib_vmul(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vmul\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = vmul(a, b);
  //printf("vmul ");
  //_print(ans);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_vneg(PyObject* self, PyObject *Py_UNUSED(ignored))
{
  _ a = ((CsclibObject*)self)->a;
  _ ans = _vneg(a);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_smul(PyObject* self, PyObject* args)
{
  int s;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &s)){
    printf("smul\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = smul(s, a);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

//share_array smod(share_t s, share_array a);

static PyObject* Csclib_smod(PyObject* self, PyObject* args)
{
  int s;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &s)){
    printf("smod\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = smod(s, a);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_AppPerm(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("AppPerm\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = AppPerm(a, b);
//  _print(ans);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_AppInvPerm(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("AppInvPerm\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;  
  _ ans = AppInvPerm(a, b);
//  _print(ans);
//  Py_INCREF(self); // test

  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_AppPerm_bits(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("AppPerm_bits\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _bits ans = AppPerm_bits(a, b);
//  _print(ans);
//  Py_INCREF(self); // test

  CsclibBObject *new_obj = (CsclibBObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}

static PyObject* Csclib_AppInvPerm_bits(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("AppInvPerm_bits\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;  
  _bits ans = AppInvPerm_bits(a, b);
//  _print(ans);
//  Py_INCREF(self); // test

  CsclibBObject *new_obj = (CsclibBObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
//  return Py_BuildValue("O", new_obj);
}



static PyObject* Csclib_A2QB(CsclibObject* self, PyObject* args)
{
  int q, qb;
  _ p = self->a;
  if (p != NULL) {
    if (!PyArg_ParseTuple(args, "ii", &q, &qb)){
      printf("A2QB\n");
      return NULL;
    }
    _pair tmp = _A2QB(p, q, qb);

    CsclibObject *new_x = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_x->a = tmp.x;
  //  Py_INCREF(new_x); // 不要?
    CsclibObject *new_y = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_y->a = tmp.y;
  //  Py_INCREF(new_y); // 不要?

  //  Py_INCREF(self); // 不要?

#if 1
    PyObject* c_list = PyList_New(2);
    PyList_SET_ITEM(c_list, 0, (PyObject*)new_x);
    PyList_SET_ITEM(c_list, 1, (PyObject*)new_y);
  //  Py_INCREF(c_list); // 不要?
    return c_list;
#else
    PyObject* tuple = Py_BuildValue("(OO)", new_x, new_y);
    return tuple;
#endif
  //  return Py_BuildValue("O", c_list);
  } else {
    Py_RETURN_NONE;
  }
}

///////////////////////////////////////////////////////////
// 位数 2 のシェアを位数 q の加法的シェアにする
///////////////////////////////////////////////////////////
static PyObject* Csclib_B2A(PyObject* self, PyObject* args)
{
  int q;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &q)){
    printf("B2A\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = B2A(a, q);

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

//////////////////////////////////////////////////////
// bits を加法的シェアに変換
//////////////////////////////////////////////////////
static PyObject* Csclib_B2A_bits(PyObject* self, PyObject* args)
{
//  int q;
//  PyObject* p;
  _bits a = ((CsclibBObject*)self)->a;
  _ ans = _B2A_bits(a);

  CsclibObject *new_obj = (CsclibObject *)CsclibType.tp_alloc(&CsclibType, 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_A2B(PyObject* self, PyObject* args)
{
  int q;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &q)){
    printf("A2B\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _bits ans = _A2B(a, q);

  CsclibBObject *new_obj = (CsclibBObject *)CsclibBType.tp_alloc(&CsclibBType, 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

#if 0
static PyObject* Csclib_A2B_(PyObject* self, PyObject* args)
{
  int q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "Oi", &p, &q)){
    printf("B2A\n");
    return NULL;
  }
  _ a = ((CsclibObject*)p)->a;
  _bits ans = _A2B(a, q);

  ((CsclibBObject*)self)->a = ans;
  Py_INCREF(self);
  return self;
}
#endif


static PyObject* Csclib_GenCycle(CsclibObject* self, PyObject* *Py_UNUSED(ignored))
{
  _ p = self->a;
  if (p != NULL) {
    _pair tmp = GenCycle(p);

    CsclibObject *new_x = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_x->a = tmp.x;
    CsclibObject *new_y = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    new_y->a = tmp.y;

    PyObject* c_list = PyList_New(2);
    PyList_SET_ITEM(c_list, 0, (PyObject*)new_x);
    PyList_SET_ITEM(c_list, 1, (PyObject*)new_y);
    return Py_BuildValue("O", c_list);
  } else {
    Py_RETURN_NONE;
  }
}


///////////////////////////////////////////////////////////
// 位数 q の加法的シェアを位数 qb の加法的シェアにする (qb > q)
///////////////////////////////////////////////////////////
static PyObject* Csclib_extend(PyObject* self, PyObject* args)
{
  int qb;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &qb)){
    printf("extend\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = _extend(a, qb);

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

///////////////////////////////////////////////////////////
// 位数 q の加法的シェアを位数 qb の加法的シェアにする (qb < q)
///////////////////////////////////////////////////////////
static PyObject* Csclib_shrink(PyObject* self, PyObject* args)
{
  int qb;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "i", &qb)){
    printf("shrink\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = _shrink(a, qb);

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}


static PyObject* Csclib_equality_bit(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vadd\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = Equality_bit(a, b);
  
  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_equality_bits(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vadd\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _bits b = ((CsclibBObject*)p)->a;
  _ ans = Equality_bits(a, b);
  
  CsclibObject *new_obj = (CsclibObject *)CsclibType.tp_alloc(&CsclibType, 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_lessthan_bit(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vadd\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ b = ((CsclibObject*)p)->a;
  _ ans = LessThan_bit(a, b);
  
  CsclibObject *new_obj = (CsclibObject*)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_lessthan_bits(PyObject* self, PyObject* args)
{
//  int n, v, q;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("vadd\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _bits b = ((CsclibBObject*)p)->a;
  _ ans = LessThan_bits(a, b);
  
  CsclibObject *new_obj = (CsclibObject *)CsclibType.tp_alloc(&CsclibType, 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_BatchAccess(PyObject* self, PyObject* args)
{
  int qb;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("BatchAccess\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ idx = ((CsclibObject*)p)->a;
  _ ans = BatchAccess(a, idx);

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_BatchAccess_bits(PyObject* self, PyObject* args)
{
  int qb;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("BatchAccess\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _ idx = ((CsclibObject*)p)->a;
  _bits ans = BatchAccess_bits(a, idx);

  CsclibBObject *new_obj = (CsclibBObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}

static PyObject* Csclib_Unary(PyObject* self, PyObject* args)
{
  int qb;
  int U;
  if (!PyArg_ParseTuple(args, "i", &U)){
    printf("Unary\n");
    return NULL;
  }
  _ a = ((CsclibObject*)self)->a;
  _ ans = Unary(a, U);

  CsclibObject *new_obj = (CsclibObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}




static PyObject* Csclib_Bprint(CsclibBObject* self, PyObject *Py_UNUSED(ignored))
{
  _bits p = self->a;
  if (p != NULL) _print_bits(p);
  Py_RETURN_NONE;
}

static PyObject* Csclib_Blen(CsclibBObject* self, PyObject *Py_UNUSED(ignored))
{
  _bits p = self->a;
  if (p != NULL) {
    return Py_BuildValue("i", p->a[0]->n);
  } else {
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_Border(CsclibBObject* self, PyObject *Py_UNUSED(ignored))
{
  _bits p = self->a;
  if (p != NULL) {
    return Py_BuildValue("i", p->a[0]->q);
  } else {
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_Bdepth(CsclibBObject* self, PyObject *Py_UNUSED(ignored))
{
  _bits p = self->a;
  if (p != NULL) {
    return Py_BuildValue("i", p->d);
  } else {
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_Bget0(CsclibBObject* self, PyObject *args)
{
  int i;
  if (!PyArg_ParseTuple(args, "i", &i)){
    printf("get\n");
    return NULL;
  }
  _bits p = (_bits)self->a;
  if (p != NULL) {
    if (i < 0 || i >= p->d) {
      printf("get i=%d d=%d\n", i, p->d);
      return NULL;
    }
    CsclibObject *new_obj = (CsclibObject *)CsclibType.tp_alloc(&CsclibType, 0);
    new_obj->a = _dup(p->a[i]);
    return (PyObject*)new_obj;
  } else {
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_Bget(CsclibBObject* self, PyObject *Py_UNUSED(ignored))
{
  int i;
  _bits p = (_bits)self->a;

  PyObject* c_list = PyList_New(p->d);
  for (int i=0; i<p->d; i++) {
    CsclibObject *new_obj = (CsclibObject *)CsclibType.tp_alloc(&CsclibType, 0);
    new_obj->a = _dup(p->a[i]);
    PyList_SET_ITEM(c_list, i, Py_BuildValue("O", new_obj));
  }
  return Py_BuildValue("O", c_list);
}

static PyObject* Csclib_Bset0(CsclibBObject* self, PyObject *args)
{
  int i;
  PyObject *q;
  if (!PyArg_ParseTuple(args, "iO", &i, &q)){
    printf("set\n");
    return NULL;
  }
  _bits p = (_bits)self->a;
  if (p != NULL) {
    if (i < 0 || i >= p->d) {
      printf("set i=%d d=%d\n", i, p->d);
      return NULL;
    }
    p->a[i] = ((_bits)q)->a[i];
    Py_RETURN_NONE;
  } else {
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_Bset(CsclibBObject* self, PyObject *args)
{
  int d;
  PyObject *c_list;
  if (!PyArg_ParseTuple(args, "O", &c_list)){
    printf("set\n");
    return NULL;
  }
  if (PyList_Check(c_list)) {
    d = PyList_Size(c_list);
  } else {
    return NULL;
  }
  NEWT(_bits, ans);
  ans->d = d;
  NEWA(ans->a, _, d);

  for (int i = 0; i < d; i++){
    CsclibObject *item = (CsclibObject *)PyList_GetItem(c_list, i);
    ans->a[i] = _dup(item->a);
  }
  CsclibBObject *new_obj = (CsclibBObject *)CsclibBType.tp_alloc(&CsclibBType, 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;

}


static PyObject* Csclib_copy_bits(PyObject* self, PyObject* args)
{
  PyObject* p;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("copy\n");
    return NULL;
  }
  _bits q = ((CsclibBObject*)p)->a;
  if (q != NULL) {
    _bits ans = _dup_bits(q);

    CsclibBObject *new_obj = (CsclibBObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
    if (new_obj == NULL) {
      printf("copy_bits null?\n");
    }
    new_obj->a = ans;
    return (PyObject*)new_obj;
  } else {
    printf("copy_bits?\n");
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}

static PyObject* Csclib_copy_bits2(PyObject* self, PyObject* args)
{
  PyObject* p;
  CsclibBObject* self2 = (CsclibBObject*)self;
  if (!PyArg_ParseTuple(args, "O", &p)){
    printf("copy\n");
    return NULL;
  }
  _bits q = ((CsclibBObject*)p)->a;
//  printf("copy_bits2\n");
//  _print_bits(q);

  if (q != NULL) {
    _bits ans = _dup_bits(q);

    if (self2->a != NULL) {
      printf("copy_bits2 free\n");
      _print_bits(self2->a);
      _free_bits(self2->a);
    }
    self2->a = ans;
    Py_INCREF(self); // 必要
    return self;
  } else {
    printf("copy_bits2?\n");
  //  Py_INCREF(self);
    Py_RETURN_NONE;
  }
}


static PyObject* Csclib_setpublic_bits(PyObject* self, PyObject* args)
{
  int i, x;
  if (!PyArg_ParseTuple(args, "ii", &i, &x)){
    printf("setpublic\n");
    return NULL;
  }
//  printf("setpublic i=%d x=%d\n", i, x);
  _bits a = ((CsclibBObject*)self)->a;
  _setpublic_bits(a, i, x);
  Py_RETURN_NONE;
}

static PyObject* Csclib_const_bits(PyObject* self, PyObject* args)
{
  int n, v, q, d;
  if (!PyArg_ParseTuple(args, "iiii", &n, &v, &q, &d)){
      printf("const_bits\n");
      return NULL;
  }
//  printf("n %d v %d q %d\n", n, v, q);
  _bits ans = share_const_bits(n, v, q, d);
  ((CsclibBObject*)self)->a = ans;
  return Py_BuildValue("O", self);
}

static PyObject* Csclib_setshare_bits(PyObject* self, PyObject* args)
{
  int i, j;
  PyObject* p;
  if (!PyArg_ParseTuple(args, "iOi", &i, &p, &j)){
    printf("setshare\n");
    return NULL;
  }
//  printf("setshare i=%d j=%d\n", i, j);

  _bits a = ((CsclibBObject*)self)->a;
  _bits b = ((CsclibBObject*)p)->a;
  _setshare_bits(a, i, b, j);
  Py_RETURN_NONE;
}

static PyObject* Csclib_slice_bits(PyObject* self, PyObject* args)
{
  int start, end;
//  PyObject* p;
  if (!PyArg_ParseTuple(args, "ii", &start, &end)){
    printf("slice\n");
    return NULL;
  }
  _bits a = ((CsclibBObject*)self)->a;
  _bits ans = _slice_bits(a, start, end);
  
  CsclibBObject *new_obj = (CsclibBObject *)Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
  new_obj->a = ans;
  return (PyObject*)new_obj;
}




static PyMethodDef Csclib_methods[] = {
    {"array", (PyCFunction)Csclib_array, METH_VARARGS},
    {"const", (PyCFunction)Csclib_const, METH_VARARGS},
    {"get", (PyCFunction)Csclib_get, METH_NOARGS},
    {"set", (PyCFunction)Csclib_set, METH_VARARGS},
    {"print", (PyCFunction)Csclib_print, METH_NOARGS},
    {"len", (PyCFunction)Csclib_len, METH_NOARGS},
    {"order", (PyCFunction)Csclib_order, METH_NOARGS},
    {"check", (PyCFunction)Csclib_check, METH_NOARGS},
    {"reconstruct", (PyCFunction)Csclib_reconstruct, METH_NOARGS},
    {"randomize", (PyCFunction)Csclib_randomize, METH_NOARGS},
    {"_dup", (PyCFunction)Csclib__dup, METH_NOARGS},
    {"_copy", (PyCFunction)Csclib_copy, METH_VARARGS},
    {"public", (PyCFunction)Csclib_public, METH_VARARGS},
//    {"getone", (PyCFunction)Csclib_getone, METH_VARARGS},
//    {"setone", (PyCFunction)Csclib_setone, METH_VARARGS},
    {"setpublic", (PyCFunction)Csclib_setpublic, METH_VARARGS},
    {"setshare", (PyCFunction)Csclib_setshare, METH_VARARGS},
    {"setshares", (PyCFunction)Csclib_setshares, METH_VARARGS},
    {"addpublic", (PyCFunction)Csclib_addpublic, METH_VARARGS},
    {"subpublic", (PyCFunction)Csclib_subpublic, METH_VARARGS},
    {"addshare", (PyCFunction)Csclib_addshare, METH_VARARGS},
    {"subshare", (PyCFunction)Csclib_subshare, METH_VARARGS},
    {"mulpublic", (PyCFunction)Csclib_mulpublic, METH_VARARGS},
    {"slice", (PyCFunction)Csclib_slice, METH_VARARGS},
    {"insert_head", (PyCFunction)Csclib_insert_head, METH_VARARGS},
    {"insert_tail", (PyCFunction)Csclib_insert_tail, METH_VARARGS},
    {"vadd", (PyCFunction)Csclib_vadd, METH_VARARGS},
    {"vsub", (PyCFunction)Csclib_vsub, METH_VARARGS},
    {"vmul", (PyCFunction)Csclib_vmul, METH_VARARGS},
    {"vneg", (PyCFunction)Csclib_vneg, METH_VARARGS},
    {"smul", (PyCFunction)Csclib_smul, METH_VARARGS},
    {"smod", (PyCFunction)Csclib_smod, METH_VARARGS},
    {"AppPerm", (PyCFunction)Csclib_AppPerm, METH_VARARGS},
    {"AppInvPerm", (PyCFunction)Csclib_AppInvPerm, METH_VARARGS},
    {"A2QB", (PyCFunction)Csclib_A2QB, METH_VARARGS},
    {"B2A", (PyCFunction)Csclib_B2A, METH_VARARGS},
    {"A2B", (PyCFunction)Csclib_A2B, METH_VARARGS},
    {"extend", (PyCFunction)Csclib_extend, METH_VARARGS},
    {"shrink", (PyCFunction)Csclib_shrink, METH_VARARGS},
    {"BatchAccess", (PyCFunction)Csclib_BatchAccess, METH_VARARGS},
    {"Unary", (PyCFunction)Csclib_Unary, METH_VARARGS},
    {"eq", (PyCFunction)Csclib_equality_bit, METH_VARARGS},
    {"lt", (PyCFunction)Csclib_lessthan_bit, METH_VARARGS},
    {"PrefixSum", (PyCFunction)Csclib_PrefixSum, METH_NOARGS},
    {"SuffixSum", (PyCFunction)Csclib_SuffixSum, METH_NOARGS},
    {"rank0", (PyCFunction)Csclib_rank0, METH_NOARGS},
    {"rank1", (PyCFunction)Csclib_rank1, METH_NOARGS},
    {"select0", (PyCFunction)Csclib_select0, METH_NOARGS},
    {"select1", (PyCFunction)Csclib_select1, METH_NOARGS},
    {"sum", (PyCFunction)Csclib_sum, METH_NOARGS},
    {"dup", (PyCFunction)Csclib__dup, METH_NOARGS},
    {"Diff", (PyCFunction)Csclib_Diff, METH_VARARGS},
    {"concat", (PyCFunction)Csclib__concat, METH_VARARGS},
    {"addall", (PyCFunction)Csclib_addall, METH_VARARGS},
    {"setperm", (PyCFunction)Csclib_setperm, METH_NOARGS},
    {"StableSort", (PyCFunction)Csclib_StableSort, METH_NOARGS},
    {"GenCycle", (PyCFunction)Csclib_GenCycle, METH_NOARGS},
    {NULL}  /* Sentinel */
};

static PyMemberDef Csclib_members[] = {
//    {"a", T_OBJECT, offsetof(CsclibObject, a), 0, "Csclib_a"},
    {NULL}  /* Sentinel */
};

static PyGetSetDef Csclib_getsetters[] = {
    {NULL}  /* Sentinel */
};

static PyTypeObject CsclibType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "csclib.Csclib_core",
    .tp_doc = PyDoc_STR("Csclib core objects"),
    .tp_basicsize = sizeof(CsclibObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc) Csclib_init,
    .tp_dealloc = (destructor) Csclib_dealloc,
    .tp_methods = Csclib_methods,
    .tp_members = Csclib_members,
};


//////////////////////////////////////////////////////////
// ビットのシェア
//////////////////////////////////////////////////////////
static PyMethodDef Csclib_Bmethods[] = {
    {"len", (PyCFunction)Csclib_Blen, METH_NOARGS},
    {"order", (PyCFunction)Csclib_Border, METH_NOARGS},
    {"depth", (PyCFunction)Csclib_Bdepth, METH_NOARGS},
    {"get", (PyCFunction)Csclib_Bget, METH_NOARGS},
    {"set", (PyCFunction)Csclib_Bset, METH_VARARGS},
    {"print", (PyCFunction)Csclib_Bprint, METH_NOARGS},
    {"setpublic", (PyCFunction)Csclib_setpublic_bits, METH_VARARGS},
    {"const", (PyCFunction)Csclib_const_bits, METH_VARARGS},
    {"setshare", (PyCFunction)Csclib_setshare_bits, METH_VARARGS},
    {"slice", (PyCFunction)Csclib_slice_bits, METH_VARARGS},
    {"B2A", (PyCFunction)Csclib_B2A_bits, METH_VARARGS},
    {"AppPerm", (PyCFunction)Csclib_AppPerm_bits, METH_VARARGS},
    {"AppInvPerm", (PyCFunction)Csclib_AppInvPerm_bits, METH_VARARGS},
    {"dup", (PyCFunction)Csclib_dup_bits, METH_NOARGS},
    {"_copy", (PyCFunction)Csclib_copy_bits, METH_VARARGS},
    {"_copy2", (PyCFunction)Csclib_copy_bits2, METH_VARARGS},
//    {"A2B", (PyCFunction)Csclib_A2B, METH_VARARGS},
    {"BatchAccess", (PyCFunction)Csclib_BatchAccess_bits, METH_VARARGS},
    {"eq", (PyCFunction)Csclib_equality_bits, METH_VARARGS},
    {"lt", (PyCFunction)Csclib_lessthan_bits, METH_VARARGS},
    {NULL}  /* Sentinel */
};

static PyMemberDef Csclib_Bmembers[] = {
//    {"a", T_OBJECT, offsetof(CsclibObject, a), 0, "Csclib_a"},
    {NULL}  /* Sentinel */
};

static void Csclib_Bdealloc(CsclibBObject *self);
static int Csclib_Binit(CsclibBObject *self, PyObject *args, PyObject *kwds);

static PyTypeObject CsclibBType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "ccsclib.Csclib_bits",
//    .tp_name = "Bits",
    .tp_doc = PyDoc_STR("Csclib bits objects"),
    .tp_basicsize = sizeof(CsclibBObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc) Csclib_Binit,
    .tp_dealloc = (destructor) Csclib_Bdealloc,
    .tp_methods = Csclib_Bmethods,
    .tp_members = Csclib_Bmembers,
};



//////////////////////////////////////////////////////////
// 初期化用
//////////////////////////////////////////////////////////
static PyTypeObject CsclibType_start = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "ccsclib.start",
    .tp_doc = PyDoc_STR("ccsclib.start objects"),
    .tp_basicsize = sizeof(CsclibObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Csclib_start,
};


//parties *_Parties;
//int _party = 0;
//long total_btn = 0, total_bt2 = 0;
//long total_perm = 0;


PyMODINIT_FUNC
PyInit_ccsclib(void) // csclib はモジュール名
{
  PyObject *m;

  m = PyModule_Create(&csclibmodule);
  if (m == NULL)
    return NULL;

  // 型 Csclib_core の作成
  if (PyType_Ready(&CsclibType) < 0)
    return NULL;
  Py_INCREF(&CsclibType);
  if (PyModule_AddObject(m, "Csclib_core", (PyObject *) &CsclibType) < 0) {
      Py_DECREF(&CsclibType);
      Py_DECREF(m);
      return NULL;
  }

  // ビット用の型の作成
  if (PyType_Ready(&CsclibBType) < 0)
    return NULL;
  Py_INCREF(&CsclibBType);
  if (PyModule_AddObject(m, "Csclib_bits", (PyObject *) &CsclibBType) < 0) {
      Py_DECREF(&CsclibBType);
      Py_DECREF(m);
      return NULL;
  }

  if (PyType_Ready(&CsclibType_start) < 0)
    return NULL;
  Py_INCREF(&CsclibType_start);
  if (PyModule_AddObject(m, "Csclib_start", (PyObject *) &CsclibType_start) < 0) {
      Py_DECREF(&CsclibType_start);
      Py_DECREF(m);
      return NULL;
  }

  return m;
}
