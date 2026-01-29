import numpy as np
import pandas as pd
from chowclassifier import Chow
import sys
import os
sys.path.append(os.path.abspath('../src'))

class small_noise_gen():
    def __init__(self, mu=0.,sigma=1e-4, n = 10000):
        self.mu = mu
        self.sigma = sigma
        self.size = n
        self.set_noise()
    def set_noise(self):
        self.noise = list(np.random.normal(loc=self.mu,scale=self.sigma, size=self.size))
    def __next__(self):
        try:
            return self.noise.pop()
        except IndexError:
            self.set_noise()
            return self.noise.pop()


def test_chow():
    """Expects perfect categorisation on quasi-perfectly aligned data"""
    X = range(0,100)
    cl = {'iI':{'bkp':50,'A':[1,2]},
            'Ii':{'bkp':50,'A':[2,1]},
            'dD':{'bkp':50,'A':[-1,-2]},
            'Dd':{'bkp':50,'A':[-2,-1]},
            'ID':{'bkp':50,'A':[1,-1]},
            'DI':{'bkp':50,'A':[-1,1]},
            'IN':{'bkp':50,'A':[1,0]},
            'NI':{'bkp':50,'A':[0,1]},
            'DN':{'bkp':50,'A':[-1,0]},
            'ND':{'bkp':50,'A':[0,-1]},
            'NN':{'bkp':50,'A':[0,0]},
            'N':{'bkp':None,'A':0},
            'D':{'bkp':None,'A':-1},
            'I':{'bkp':None,'A':1}}
    sng = small_noise_gen()
    p = 0
    i = 0
    for k,v in cl.items():
        if v['bkp'] is None:
            df = pd.DataFrame(zip(X,[v['A']*x*2+0 + next(sng) for x in X]), columns = ['year','value'])
        else:
            if k == 'NN':
                b = 1
            else:
                b = v['bkp'] * v['A'][0]
            y = [v['A'][0]*x*2 + 0 + next(sng) for x in X if x < v['bkp']] +\
                      [v['A'][1]*x*2 + b + next(sng) for x in X if x >= v['bkp']]
            df = pd.DataFrame(zip(X,y), columns = ['year','value'])
        C = Chow(df = df,margin = 50)
        C.run()
        p+=int(C.treeclass == k)
        i+=1
    assert p/float(i) > 0.99, f"Divergence in test_chow, found true class with rate {p}."
    
    

            