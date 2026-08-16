#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>

typedef void* EGLDisplay;
typedef void* EGLConfig;
typedef void* EGLSurface;
typedef void* EGLContext;
typedef void* EGLNativeWindowType;
typedef int EGLBoolean;
typedef int EGLint;
typedef unsigned int GLenum;
typedef unsigned int GLbitfield;
typedef int GLsizei;
typedef int GLint;
typedef void (*EGLProc)(void);

static FILE *lf = NULL;
static void trace_log(const char *fmt, ...) {
    if (!lf) {
        const char *p = getenv("DARKFATE_EGL_TRACE_LOG");
        if (p && *p) lf = fopen(p, "a");
        if (!lf) lf = stderr;
        setvbuf(lf, NULL, _IOLBF, 0);
    }
    va_list ap; va_start(ap, fmt); vfprintf(lf, fmt, ap); va_end(ap);
    fputc('\n', lf);
}

#define RESOLVE(name, type) static type real_##name = NULL; if (!real_##name) real_##name = (type)dlsym(RTLD_NEXT, #name)

EGLSurface eglCreateWindowSurface(EGLDisplay dpy, EGLConfig cfg, EGLNativeWindowType win, const EGLint *attrs) {
    typedef EGLSurface (*fn)(EGLDisplay,EGLConfig,EGLNativeWindowType,const EGLint*);
    RESOLVE(eglCreateWindowSurface, fn);
    EGLSurface s = real_eglCreateWindowSurface ? real_eglCreateWindowSurface(dpy,cfg,win,attrs) : NULL;
    trace_log("TRACE eglCreateWindowSurface dpy=%p cfg=%p win=%p -> %p", dpy,cfg,win,s);
    return s;
}

EGLContext eglCreateContext(EGLDisplay dpy, EGLConfig cfg, EGLContext share, const EGLint *attrs) {
    typedef EGLContext (*fn)(EGLDisplay,EGLConfig,EGLContext,const EGLint*);
    RESOLVE(eglCreateContext, fn);
    EGLContext c = real_eglCreateContext ? real_eglCreateContext(dpy,cfg,share,attrs) : NULL;
    trace_log("TRACE eglCreateContext dpy=%p cfg=%p share=%p -> %p", dpy,cfg,share,c);
    return c;
}

EGLBoolean eglMakeCurrent(EGLDisplay dpy, EGLSurface draw, EGLSurface read, EGLContext ctx) {
    typedef EGLBoolean (*fn)(EGLDisplay,EGLSurface,EGLSurface,EGLContext);
    RESOLVE(eglMakeCurrent, fn);
    EGLBoolean r = real_eglMakeCurrent ? real_eglMakeCurrent(dpy,draw,read,ctx) : 0;
    trace_log("TRACE eglMakeCurrent dpy=%p draw=%p read=%p ctx=%p -> %d", dpy,draw,read,ctx,r);
    return r;
}

EGLBoolean eglSwapBuffers(EGLDisplay dpy, EGLSurface surf) {
    typedef EGLBoolean (*fn)(EGLDisplay,EGLSurface);
    RESOLVE(eglSwapBuffers, fn);
    EGLBoolean r = real_eglSwapBuffers ? real_eglSwapBuffers(dpy,surf) : 0;
    static unsigned long n=0; n++;
    if (n <= 120 || (n % 120)==0) trace_log("TRACE eglSwapBuffers #%lu dpy=%p surf=%p -> %d", n,dpy,surf,r);
    return r;
}

EGLBoolean eglSwapInterval(EGLDisplay dpy, EGLint interval) {
    typedef EGLBoolean (*fn)(EGLDisplay,EGLint);
    RESOLVE(eglSwapInterval, fn);
    EGLBoolean r = real_eglSwapInterval ? real_eglSwapInterval(dpy,interval) : 0;
    trace_log("TRACE eglSwapInterval dpy=%p interval=%d -> %d", dpy,interval,r);
    return r;
}

EGLBoolean eglQuerySurface(EGLDisplay dpy, EGLSurface surf, EGLint attr, EGLint *value) {
    typedef EGLBoolean (*fn)(EGLDisplay,EGLSurface,EGLint,EGLint*);
    RESOLVE(eglQuerySurface, fn);
    EGLBoolean r = real_eglQuerySurface ? real_eglQuerySurface(dpy,surf,attr,value) : 0;
    if (attr==0x3057 || attr==0x3056) trace_log("TRACE eglQuerySurface attr=0x%x -> r=%d value=%d", attr,r,value?*value:-999);
    return r;
}

EGLint eglGetError(void) {
    typedef EGLint (*fn)(void);
    RESOLVE(eglGetError, fn);
    EGLint e = real_eglGetError ? real_eglGetError() : 0x3000;
    if (e != 0x3000) trace_log("TRACE eglGetError -> 0x%x", e);
    return e;
}

void glClearColor(float r,float g,float b,float a) {
    typedef void (*fn)(float,float,float,float);
    RESOLVE(glClearColor, fn);
    static unsigned long n=0; n++;
    if (n<=20) trace_log("TRACE glClearColor #%lu %.3f %.3f %.3f %.3f",n,r,g,b,a);
    if (real_glClearColor) real_glClearColor(r,g,b,a);
}

void glClear(GLbitfield mask) {
    typedef void (*fn)(GLbitfield);
    RESOLVE(glClear, fn);
    static unsigned long n=0; n++;
    if (n<=60 || (n%120)==0) trace_log("TRACE glClear #%lu mask=0x%x",n,mask);
    if (real_glClear) real_glClear(mask);
}

void glDrawArrays(GLenum mode, GLint first, GLsizei count) {
    typedef void (*fn)(GLenum,GLint,GLsizei);
    RESOLVE(glDrawArrays, fn);
    static unsigned long n=0; n++;
    if (n<=60 || (n%240)==0) trace_log("TRACE glDrawArrays #%lu mode=0x%x first=%d count=%d",n,mode,first,count);
    if (real_glDrawArrays) real_glDrawArrays(mode,first,count);
}

void glDrawElements(GLenum mode, GLsizei count, GLenum type, const void *indices) {
    typedef void (*fn)(GLenum,GLsizei,GLenum,const void*);
    RESOLVE(glDrawElements, fn);
    static unsigned long n=0; n++;
    if (n<=60 || (n%240)==0) trace_log("TRACE glDrawElements #%lu mode=0x%x count=%d type=0x%x",n,mode,count,type);
    if (real_glDrawElements) real_glDrawElements(mode,count,type,indices);
}

EGLProc eglGetProcAddress(const char *name) {
    typedef EGLProc (*fn)(const char*);
    RESOLVE(eglGetProcAddress, fn);
    EGLProc p = real_eglGetProcAddress ? real_eglGetProcAddress(name) : NULL;
    static unsigned long n=0; n++;
    if (n<=160) trace_log("TRACE eglGetProcAddress #%lu %s -> %p", n, name?name:"(null)", p);
    if (!name) return p;
    if (!strcmp(name,"eglCreateWindowSurface")) return (EGLProc)eglCreateWindowSurface;
    if (!strcmp(name,"eglCreateContext")) return (EGLProc)eglCreateContext;
    if (!strcmp(name,"eglMakeCurrent")) return (EGLProc)eglMakeCurrent;
    if (!strcmp(name,"eglSwapBuffers")) return (EGLProc)eglSwapBuffers;
    if (!strcmp(name,"eglSwapInterval")) return (EGLProc)eglSwapInterval;
    if (!strcmp(name,"eglQuerySurface")) return (EGLProc)eglQuerySurface;
    if (!strcmp(name,"eglGetError")) return (EGLProc)eglGetError;
    if (!strcmp(name,"glClearColor")) return (EGLProc)glClearColor;
    if (!strcmp(name,"glClear")) return (EGLProc)glClear;
    if (!strcmp(name,"glDrawArrays")) return (EGLProc)glDrawArrays;
    if (!strcmp(name,"glDrawElements")) return (EGLProc)glDrawElements;
    return p;
}
