"""
The DFT grids are a little different in pyquante2 from pyquante1. Here we are
only storing the points and the weights, and we will use other data objects to
store, say, the density, the basis functions, or the various gradients at each
point.
"""
import numpy as np
from pyquante2.grid.atomic_grid import atomic_grid

class grid(object):
    def __init__(self,atoms,**kwargs):
        agrids = [atomic_grid(atom,**kwargs) for atom in atoms]
        becke_reweight_atoms(atoms,agrids)
        self.points = np.vstack([agrid.points for agrid in agrids])
        self.npts,sb4 = self.points.shape
        assert sb4==4
        return

    def __len__(self): return self.ng
    def __getitem__(self,*args): self.points.__getitem__(*args)

    def setbfamps(self,bfs):
        nbf = len(bfs)
        self.bfamps = np.zeros((self.npts,nbf),'d')
        for j,bf in enumerate(bfs):
            for i,(x,y,z,w) in enumerate(self.points):
                self.bfamps[i,j] = bf(x,y,z)
        return

    def getdens_naive(self,D):
        # Naive version of getdens
        rho = np.zeros(self.npts,'d')
        for i,pt in enumerate(self.points):
            bfs = self.bfamps[i,:]
            rho[i] = 2*np.dot(bfs,np.dot(D,bfs))
        return rho
            
    def getdens(self,D):
        return 2*np.einsum('pI,pJ,IJ->p',self.bfamps,self.bfamps,D)

    def getdens_interpolated(self,D,bbox,npts=50):
        from scipy.interpolate import griddata
        xmin,xmax,ymin,ymax,zmin,zmax = bbox
        xi,yi,zi = np.mgrid[xmin:xmax:(npts*1j),ymin:ymax:(npts*1j),zmin:zmax:(npts*1j)]
        rho = self.getdens(D)
        return griddata(self.points[:,:3],rho,(xi,yi,zi))

def becke_reweight_atoms(atoms,agrids,**kwargs):
    for iat,agrid in enumerate(agrids):
        for i in range(agrid.npts):
            xyzp = agrid.points[i,:3]
            Ps = [becke_atomic_grid_p(atj,xyzp,atoms,**kwargs) for atj in atoms]
            P = Ps[iat]/sum(Ps)
            agrid.points[i,3] = P*agrid.points[i,3]
    return

def becke_atomic_grid_p(ati,xyzp,atoms,**kwargs):
    from pyquante2.grid.data import Bragg
    do_becke_hetero = kwargs.get('do_becke_hetero',True)
    sprod = 1
    rip = np.linalg.norm(ati.r-xyzp)
    for atj in atoms:
        if ati == atj: continue
        rij = np.linalg.norm(ati.r-atj.r)
        rjp = np.linalg.norm(atj.r-xyzp)
        mu = (rip-rjp)/rij
        # Modify mu based on Becke hetero formulas (App A)
        if do_becke_hetero and ati.atno != atj.atno:
            chi = Bragg[ati.atno]/Bragg[atj.atno]
            u = (chi-1.)/(chi+1.)
            a = u/(u*u-1)
            a = min(a,0.5)
            a = max(a,-0.5)
            mu += a*(1-mu*mu)
        sprod *= sbecke(mu)
    return sprod

def fbecke(x,n=3):
    for i in range(n): x = pbecke(x)
    return x
def pbecke(x): return 1.5*x-0.5*pow(x,3)
def sbecke(x,n=3): return 0.5*(1-fbecke(x,n))

def test_mesh():
    from pyquante2 import h2o
    return grid(h2o)

if __name__ == '__main__':
    mesh = test_mesh()
