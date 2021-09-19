'''
IdealFlowNetwork.py

Ideal Flow Network Core Library

version 0.9

@author: Kardi Teknomo
http://people.revoledu.com/kardi/

(c) 2014-2021 Kardi Teknomo
Available in https://github.com/teknomo/IdealFlowNetwork
'''
import numpy as np
from fractions import Fraction
from math import gcd
from scipy import sparse


def lcm(a,b):
    '''
    return least common multiple of large numbers
    '''
    return a*b // gcd(a,b)


def capacity2adj(C):
    '''
    convert capacity matrix to adjacency matrix
    '''
    return(np.asarray(C)>0).astype(int) # get adjacency matrix structure


def capacity2stochastic(C):
    '''
    convert capacity matrix into stochastic matrix
    S=C./(sR*ones(1,n))
    '''
    C=sparse.csc_matrix(C)
    n=C.shape[0]
    sR=sparse.csc_matrix(C.sum(axis=1))
    jT=sparse.csc_matrix(np.ones((1,n)))
    B=sR.dot(jT)
    return C/B


def adj2stochastic(A):
    '''
    convert adjacency matrix to stochastic matrix 
    of equal outflow distribution
    '''
    v=np.sum(A,axis=1)           # node out degree
    D=np.diag(v)                 # degree matrix
    return np.dot(np.linalg.inv(D),A) # ideal flow of equal outflow distribution


def idealFlow2stochastic(F):
    '''
    convert ideal flow matrix into Markov stochastic matrix
    ''' 
    s=np.apply_along_axis(np.sum, axis=1, arr=F)
    return F/s[:,np.newaxis]


def steadyStateMC(S,kappa=1):
    '''
    convert stochastic matrix into steady state Markov vector
    kappa is the total of Markov vector
    '''
    [m,n]=S.shape
    if m==n:
        I=np.eye(n)
        j=np.ones((1,n))
        X=np.concatenate((np.subtract(S.T,I), j), axis=0) # vstack
        Xp=np.linalg.pinv(X)      # Moore-Penrose inverse
        y=np.zeros((m+1,1),float)
        y[m]=kappa
        return np.dot(Xp,y) 


def idealFlow(S,pi):
    '''
    return ideal flow matrix
    based on stochastic matrix and Markov vector
    '''
    [m,n]=S.shape
    jT=np.ones((1,n))
    return np.multiply(np.dot(pi,jT),S)


def adj2idealFlow(A,kappa=1):
    '''
    convert adjacency matrix into ideal flow matrix 
    of equal distribution of outflow 
    kappa is the total flow
    '''
    S=adj2stochastic(A)
    pi=steadyStateMC(S,kappa)
    return idealFlow(S,pi)
    
    
def capacity2idealFlow(C,kappa=1):
    '''
    convert capacity matrix into ideal flow matrix
    kappa is the total flow
    '''
    S=capacity2stochastic(C)
    pi=steadyStateMC(S,kappa)
    return idealFlow(S,pi)


def sumOfRow(M):
    '''
    return vector sum of rows
    '''
    [m,n]=M.shape
    j=np.ones((m,1))
    return np.dot(M,j)    


def sumOfCol(M):
    '''
    return row vector sum of columns
    '''
    [m,n]=M.shape
    j=np.ones((1,n))
    return np.dot(j,M)


def isSquare(M):
    '''
    return True if M is a square matrix
    '''
    [m,n]=M.shape
    if m==n:
        return True
    else:
        return False


def isNonNegative(M):
    '''
    return True of M is a non-negative matrix
    '''
    if np.any(M<0):
        return False
    else:
        return True


def isPositive(M):
    '''
    return True of M is a positive matrix
    '''
    if np.any(M<=0):
        return False
    else:
        return True
        

def isPremagic(M):
    '''
    return True if M is premagic matrix
    '''
    sC=sumOfCol(M)
    sR=sumOfRow(M)
    mR,mC=M.shape
    d=np.linalg.norm(np.subtract(sC,sR.T))
    if d<=1000*mR*mC*np.finfo(float).eps:
        return True
    else:
        return False
    

def isIrreducible(M):
    '''
    return True if M is irreducible matrix 
    '''
    if isSquare(M) and isNonNegative(M):
        [m,n]=M.shape
        I=np.eye(n)
        Q=np.linalg.matrix_power(np.add(I,M),n-1) # Q=(I+M)^(n-1)
        return isPositive(Q)
    else:
        return False


def isIdealFlow(M):
    '''
    return True if M is an ideal flow matrix
    '''
    if isNonNegative(M) and isIrreducible(M) and isPremagic(M):
        return True
    else:
        return False


def networkEntropy(S):
    '''
    return the value of network entropy
    '''
    s=S[np.nonzero(S)]
    return np.sum(np.multiply(-s,np.log(s)),axis=None)


def entropyRatio(S):
    '''
    return network entropy ratio
    '''
    h1=networkEntropy(S)
    A=(S>0).astype(int) # get adjacency matrix structure
    T=adj2stochastic(A)
    h0=networkEntropy(T)
    return h1/h0


def equivalentIFN(F,scaling):
    '''
    return scaled ideal flow matrix
    input:
    F = ideal flow matrix
    scaling = global scaling value
    '''
    F1=F*scaling
    return F1
    

def globalScaling(F,scalingType='min',val=1):
    '''
    return scaling factor to ideal flow matrix
    to get equivalentIFN
    input:
    F = ideal flow matrix
    scalingType = {'min','max','sum','int'}
    val = value of the min, max, or sum
    'int' means basis IFN (minimum integer)
    '''
    f=np.ravel(F[np.nonzero(F)]) # list of non-zero values in F
    # print('f',f)
    if scalingType=='min':
        opt=min(f)
        scaling=val/opt
    elif scalingType=='max':
        scaling=val/max(f)
    elif scalingType=='sum':
        scaling=val/sum(f)
    elif scalingType=='int':
        denomSet=set()
        for g in f:
            h=Fraction(g).limit_denominator(1000000000)
            denomSet.add(h.denominator)
        scaling=1
        for d in denomSet:
            scaling=lcm(scaling,d)
    else:
        raise ValueError("unknown scalingType")
    return scaling
    



if __name__=='__main__':
    C=[[0, 1, 1, 1, 0],      # a
       [0, 0, 0, 1, 0],      # b
       [0, 1, 1, 0, 0],      # c
       [0, 0, 0, 0, 2],      # d
       [1, 0, 1, 2, 0]]      # e
    A=capacity2adj(C)
    print('A:\n',A)
    S=capacity2stochastic(C)
    print('S:',S)
    F=capacity2idealFlow(C)
    print('F:\n',F)
    scaling=globalScaling(F,'int')
    F=equivalentIFN(F,scaling)
    print('scaled F:\n',F)
    print("is Premagic F?",isPremagic(F))

