#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 17 09:54:59 2018

@author: bruce
"""

import csv
import time
import numpy as np

from SMMSAT.cython_func.block_loop import *
from SMMSAT.cython_func.listloop import *
from analysis.analysis import *
import math_tool 


class structure_factor(Analysis):
    def __init__(self,List,filename,n_bins,MaxDistance):
        self.List=List
        self.filename=filename
        self.n_bins=n_bins

        if MaxDistance > 0 and MaxDistance < min(self.List.System.c_AbsBoxSize[0],self.List.System.c_AbsBoxSize[1],self.List.System.c_AbsBoxSize[2])/2:
            self.MaxDistance=MaxDistance
        else:
            self.MaxDistance=min(self.List.System.c_AbsBoxSize[0],self.List.System.c_AbsBoxSize[1],self.List.System.c_AbsBoxSize[2])/2
        
        self.dr=self.MaxDistance/self.n_bins
        self.hist_bins=[self.dr*i for i in range(n_bins+1)]
        self.rdf=np.zeros(self.List.System.c_NumberBlocks,dtype=np.ndarray)
        self.weighting=np.zeros(self.List.System.c_NumberBlocks)
        self.rho=self.List.wrap_pos.shape[0]/self.List.System.c_DataFrame.c_NumberFrames/np.power(min(self.List.System.c_AbsBoxSize[0],self.List.System.c_AbsBoxSize[1],self.List.System.c_AbsBoxSize[2]),3)
        print("\nRadial Distribution Function "+str(n_bins)+" "+str(MaxDistance))

    def excute_Analysis(self):
        print("\nCalculating radial distribution function.\n")
        start=time.time()
        block_loop(self,self.List.wrap_pos)
        self.postprocess_list()
        self.write()
        print("Writing rdf to file "+self.filename)
        end=time.time()
        print("\nCalculated radial distribution function in " +"{0:.2f}".format(end-start) +" seconds.")
    
    def list_statickernel(self,block,current_trajectory):
        result=ListLoop(self,current_trajectory)
        gr=np.sum(np.array(result)[:,0],axis=0)
        self.weighting[block]+=1
        self.rdf[block]=gr/current_trajectory.shape[0]/self.rho
        for index_bin in range(self.n_bins):
            r_inner=self.dr*(index_bin)
            r_outer=self.dr*(index_bin+1)
            dv=4./3.*np.pi*(np.power(r_outer,3) - np.power(r_inner,3))
            self.rdf[block][index_bin]=self.rdf[block][index_bin]/dv

    def listkernel(self,atomii,Trj):
        dx_pbc=np.power(Trj[atomii][0]-Trj[:,0]-np.round((Trj[atomii][0]-Trj[:,0])/(self.List.System.c_AbsBoxSize[0]))*(self.List.System.c_AbsBoxSize[0]),2)
        dy_pbc=np.power(Trj[atomii][1]-Trj[:,1]-np.round((Trj[atomii][1]-Trj[:,1])/(self.List.System.c_AbsBoxSize[1]))*(self.List.System.c_AbsBoxSize[1]),2)
        dz_pbc=np.power(Trj[atomii][2]-Trj[:,2]-np.round((Trj[atomii][2]-Trj[:,2])/(self.List.System.c_AbsBoxSize[2]))*(self.List.System.c_AbsBoxSize[2]),2)
        distance=np.sqrt(dx_pbc+dy_pbc+dz_pbc)
        distance[atomii] = 100000000000.0
        (hist,bins)=np.histogram(distance,bins=self.hist_bins,normed=False)
        hist=hist.astype(float)
        result=np.array([hist,bins])
        return result

    def postprocess_list(self):
        self.rdf=np.sum(self.rdf,axis=0)/np.sum(self.weighting)

    def write(self):
        RDF_file=open(self.filename+".csv","w")
        with RDF_file:
            writer=csv.writer(RDF_file,delimiter='\t',
                            quotechar='\t', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["RDF data created by SMMSAT "+self.List.System.Version])
            for index in range(self.n_bins):
                writer.writerow(["{0:.4f}".format(self.hist_bins[index]),("{0:."+str(math_tool.data_precision)+"f}").format(self.rdf[index])])