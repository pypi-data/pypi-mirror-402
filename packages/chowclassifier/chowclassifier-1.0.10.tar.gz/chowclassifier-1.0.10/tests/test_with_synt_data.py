"""Tests"""
import string
import numpy as np
import pandas as pd
from chowclassifier import ChewData
import sys
import os
sys.path.append(os.path.abspath('../src'))

def labels(alphabet=string.ascii_uppercase):
    assert len(alphabet) == len(set(alphabet))  # make sure every letter is unique
    s = [alphabet[0]]
    while 1:
        yield ''.join(s)
        l = len(s)
        for i in range(l-1, -1, -1):
            if s[i] != alphabet[-1]:
                s[i] = alphabet[alphabet.index(s[i])+1]
                s[i+1:] = [alphabet[0]] * (l-i-1)
                break
        else:
            s = [alphabet[0]] * (l+1)

class yield_param():
    def __init__(self,func,**params):
        self.A = list(func(**params)) # generate param
    def __next__(self):
        return self.A.pop(0)

def synt_series(X,
                a, b, r,
                seed = None):
    """Generate a random series"""
    if seed:
        np.random.seed(seed)
    mu = 0
    sigma = np.random.gamma(1,1,1)
    ng = np.random.normal(mu, sigma, len(X)*r)
    return [x*a+b for x in X for i in range(0,r)] + ng

def classify(a,b,bkp, z = 1e-2):
    if bkp is not None:
        if a[0]>z and a[1]>z and a[0]>a[1]:
            return 'Ii'
        elif a[0]>z and a[1]>z and a[0]<=a[1]:
            return 'iI'
        elif a[0]<-z and a[1]<-z and a[0]>a[1]:
            return 'Dd'
        elif a[0]<-z and a[1]<-z and a[0]<=a[1]:
            return 'dD'
        elif a[0]>z and a[1]<-z:
            return 'ID'
        elif a[0]>z and a[1]>-z and a[1]<z:
            return 'IN'
        elif a[0]<-z and a[1]>-z and a[1]<z:
            return 'DN'
        elif a[0]<-z and a[1]>z:
            return 'DI'
        elif a[1]>z and a[0]>-z and a[0]<z:
            return 'NI'
        elif a[1]<-z and a[0]>-z and a[0]<z:
            return 'ND'
        elif a[0]>-z and a[0]<z and a[1]>-z and a[1]<z:
            return 'NN'
    else:
        if a > z:
            return 'I'
        elif a < -z:
            return 'D'
        else:
            return 'N'

def synt_data(n=1000,m=50,seed = None):
    X = np.linspace(0,n,2*n+2)
    labs = labels()
    r = 3
    data = {'year':[x for x in X for i in range(0,r)]}
    exp = {}
    with_breakpoints = np.random.binomial(1,0.8,m)# flip coin to see if broken at bkp (favour breaking)
    bks = [x if y == 1 else None for x,y in zip(np.random.choice(range(5,len(X)-5),m),with_breakpoints)]# select random breakpoints
    nparams = m + sum(with_breakpoints) # total number of pairs of parameters needed
    A = yield_param(np.random.normal,loc=0,scale=1,size=nparams) # slope gen
    b = yield_param(np.random.poisson,lam=15,size=m) # intercept gen
    for i in range(0,m):
        l = next(labs)
        bk = bks[i]
        if bk is not None:
            a1, b1 = next(A),next(b)
            a2 = next(A)
            b2 = a2 * bk + b1
            s1 = synt_series(X[:bk],a1,b1,r,seed = seed)
            s2 = synt_series(X[bk:],a2,b2,r,seed = seed)
            series = np.concatenate((s1,s2))
            tt = classify((a1,a2),(b1,b2),bkp=bk)
            bk = X[bk]
        else:# else no breakpoint
            bk = None
            # generate random slope and intercept
            a0 = next(A)
            b0 = next(b)
            tt = classify(a0,b0,bkp=bk)
            # generate random series with picked slope and intercept
            series =synt_series(X,a0,b0,r,seed = seed)
        data[l] = series 
        exp[l] = {'tt':tt,'bkp':bk}
    df = pd.DataFrame(data)
    return df,exp

def test_synt_data():
    sdf,exp = synt_data(n=40,m=50)
    C = ChewData(sdf, margin = 60)
    C.run(breakpoint = None)
    res = pd.DataFrame(columns = ['tt','bk','ett','ebk','acc'])
    for c in C.chows:
        if c.treeclass == exp[c.name]['tt']:
            acc = 0
        elif c.breakpoint is not None and exp[c.name]['bkp'] is None:
            if c.treeclass.upper()[0]==exp[c.name]['tt']:
                if c.treeclass.upper()[1]==exp[c.name]['tt']:
                    acc = 1
                else:
                    acc = 2
            elif c.treeclass.upper()[1]==exp[c.name]['tt']:
                acc = 2
            else:
                acc = 4
        elif c.breakpoint is None and exp[c.name]['bkp'] is not None:
            if exp[c.name]['tt'].upper()[0]==c.treeclass:
                if exp[c.name]['tt'].upper()[1]==c.treeclass:
                    acc = 1
                else:
                    acc = 2
            elif exp[c.name]['tt'].upper()[1]==c.treeclass:
                acc = 2
            else:
                acc = 4
        elif c.breakpoint is not None and exp[c.name]['bkp'] is not None:
            if exp[c.name]['tt'].upper()[0]==c.treeclass.upper()[0]:
                if exp[c.name]['tt'].upper()[1]==c.treeclass.upper()[1]:
                    acc = 1
                else:
                    acc = 2
            elif exp[c.name]['tt'].upper()[1]==c.treeclass.upper()[1]:
                acc = 2
            else:
                acc = 4
        else:
            acc = 4
        res.loc[len(res)] = [c.treeclass,c.breakpoint,
                                exp[c.name]['tt'],#expected class
                                exp[c.name]['bkp'],#expected breakpoint
                                acc] # acc = 0 means correct assignment.
    res['acc_bk'] = [v['bk'] == v['ebk'] if v['bk'] is not None and v['ebk'] is not None else True for i,v in res.iterrows()]
    assert sum(res['acc_bk'])/len(res) > 0.85, f"Got wrong breakpoint accurary, {sum(res['acc_bk'])/len(res)}"
    assert sum(res['acc'])/len(res) < 0.6, f"Got many missmatch {res.loc[res['tt']!=res['ett'],:]}"


