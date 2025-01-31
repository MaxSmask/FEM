import scipy.sparse as sp
import numpy as np
import matplotlib.pyplot as plt

def conelmtab(x0, L, noelms):
    VX = np.linspace(x0, x0+L, noelms+1)
    idxs = np.arange(noelms+1)
    EToV = np.vstack((idxs[:-1], idxs[1:])).T

    return VX, EToV

def assembly1D(VX, EToV, D, qt, t):
    N = len(EToV[:,1])
    M = N+1

    nnzmax = 4*N
    ii = np.zeros(nnzmax, dtype=int)
    jj = np.zeros(nnzmax, dtype=int)
    r = np.zeros(nnzmax)    # Corresponds to A
    s = np.zeros(nnzmax)    # Corresponds to C
    b = np.zeros(M)
    count = 0
    
    for nn in range(N):
        # Save element information
        i = EToV[nn,0]
        j = EToV[nn,1]

        xi = VX[i]
        xj = VX[j]

        h = xj - xi

        qtilde = h/4*(qt(t,xi)+qt(t,xj))

        b[[i,j]] += qtilde


        ii[count:count + 4] = [i, i, j, j]
        jj[count:count + 4] = [i, j, j, i]
        r[count:count + 4] = list(np.array([D/h,-D/h,D/h,-D/h]))
        s[count:count + 4] = list(np.array([h/3,h/6,h/3,h/6]))
        
        count += 4


    R = sp.csr_matrix((r[:count], (ii[:count], jj[:count])), shape=(M, M))
    S = sp.csr_matrix((s[:count], (ii[:count], jj[:count])), shape=(M, M))


    return R,S,b

def dirbc1D(f, R,S, b):
    d = np.zeros(len(b))

    # Boundary conditions
    # i = 0, j = 1
    temp = R[0,1]*f[0]
    
    b[0] = d[0] = 0

    b[1] -= temp
    d[1] += temp

    # Modify R and S
    R[0,0] = R[1,0] = R[0,1] = 0

    S[0,0] = 1
    S[1,0] = S[0,1] = 0
    
    # i = N-1, j = N-2
    temp = R[-2,-1]*f[-1]

    b[-1] = d[-1] = 0

    b[-2] -= temp
    d[-2] += temp

    R[-1,-1] = R[-1,-2] = R[-2,-1] = 0
    
    S[-1,-1] = 1
    S[-1,-2] = S[-2,-1] = 0

    return R,S,b,d

   
def RS_1D(R,S,dt,d2):
    S -= d2*R
    R = S + dt*R 

    return R,S


# Step 4 Factor but we don't.

def construct_e(S,b,un,d2):
    return S@un + d2*b


# Step 7 + 8
def advance_b(d,EToV, qt,tnext):
    bnext = np.zeros(len(EToV[:,0])+1)

    for elm in EToV:
        # Save element information
        i = elm[0]
        j = elm[1]

        xi = VX[i]
        xj = VX[j]

        h = xj - xi

        qtilde = h/4*(qt(tnext,xi)+qt(tnext,xj))

        bnext[[i,j]] += qtilde

    bnext[0] = bnext[-1] = 0
    bnext -= d

    return bnext

# Step 9
def update_e(e,bnext,d1):
    return e + d1*bnext    
    

def oneit(VX, EToV, f, D, qt, t0,dt,un,theta):
    d1, d2 = dt*theta, dt*(1-theta)

    # Step 1: Assemble R, S and b
    R, S, b = assembly1D(VX, EToV, D, qt, t0)

    # Step 2: Dirichlet BC
    R,S, b, d = dirbc1D(f, R,S, b)

    # Compute d1, d2

    # Step 3: Overwrite R and S
    R,S = RS_1D(R,S,dt,d2)

    # Step 5 + 6: Construct e

    e = construct_e(S,b,un,d2)

    # Step 7 + 8: Advance b
    b = advance_b(d,EToV, qt,t0+dt)

    # Step 9: compute e
    e = update_e(e,b,d1)


    # Step 10: Solve!
    unext = sp.linalg.spsolve(R,e)

    return unext

## Testcase:
n = 2
VX, EToV = conelmtab(0,np.pi,n)

D = 1
qt = lambda t,x: 0

t0 = 0
f = [0,0]

un = np.sin(VX)

theta = 1.0
dt = 0.1

A,C,b = assembly1D(VX, EToV, D, qt, t0)

#%%

unext = oneit(VX, EToV, f, D, qt, t0,dt,un,theta)

plt.figure()
plt.plot(VX,un,label="u0")
plt.plot(VX,unext,label="unext")
plt.plot(VX,un*np.exp(-dt), label="True")
plt.legend()
plt.show()


#%% Time Convergence test


def u_true(x,t):
    return np.sin(x)*np.exp(-D*t)


N = list(range(2,50))
error = np.zeros(len(N))


for i,n in enumerate(N):

    unext = un
    
    t = 0
    T = 0.5
    dt = T/n
    while t < T:
        unext = oneit(VX, EToV, f, D, qt, t ,dt,unext,theta)    
        t += dt
    
    error[i] = np.linalg.norm(unext - u_true(VX,t),np.inf) 

h = T/np.array(N)

plt.figure()
plt.plot(np.log(h),np.log(error),label="error")
plt.xlabel("Error")
plt.ylabel("Step Size: dt")
plt.show()

a,b = np.polyfit(np.log(h)[-20:],np.log(error)[-20:],1)

#%%



