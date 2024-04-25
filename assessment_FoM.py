import numpy as np
from numpy import ndarray

def assessment_FoM(before_landuse_list:list,after_landuse_list:list,simulated_landuse_list:list,areas:ndarray)->tuple:
    '''
    ### Abstract
        Calculate FoM,UA,PA accuracy
    ### Parameters
        - before_landuse_list：List of previous land uses
        - after_landuse_list：Late land use list
        - simulated_landuse_list：List of land use simulation results
        - areas：Area of all plots

    ### Return
        FoM，PA，UA
    '''
    landuse_count=len(before_landuse_list)

    '''
        A: The actual changes and the simulation results do not change
        B: The actual changes occur and the simulation results are correct
        C: The actual changes and the simulation results change and the simulation results are incorrect
        D: There is no actual change and the simulation results change
    '''
    A,B,C,D=0,0,0,0
    for i in range(landuse_count):
        before_landuse=before_landuse_list[i]
        after_landuse=after_landuse_list[i]
        simulated_landuse=simulated_landuse_list[i]
        area=areas[i]

        if before_landuse!=after_landuse and before_landuse==simulated_landuse:
            A+=area
        if before_landuse!=after_landuse and after_landuse==simulated_landuse:
            B+=area
        if before_landuse!=after_landuse and before_landuse!=simulated_landuse and after_landuse!=simulated_landuse:
            C+=area
        if before_landuse==after_landuse and before_landuse!=simulated_landuse:
            D+=area

    FoM=B/(A+B+C+D)
    PA=B/(A+B+C)
    UA=B/(B+C+D)

    return FoM,PA,UA
