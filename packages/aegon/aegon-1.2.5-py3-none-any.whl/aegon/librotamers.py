import random
import numpy as np
import networkx as nx
from ase import Atoms
from aegon.libutils import adjacency_matrix, rodrigues_rotation_matrix, rotate_vector_angle_deg, rename
#-------------------------------------------------------------------------------
zeta=np.array([0.0, 0.0, 1.0])
zero=np.array([0.0, 0.0, 0.0])
ndigit=5
#-------------------------------------------------------------------------------
def get_bridge_left_right(adjmatrix):
    G = nx.from_numpy_array(adjmatrix)
    bridges = list(nx.bridges(G))
    all=[]
    for bridge in bridges:
        [u, v] = bridge
        G_temp = G.copy()
        G_temp.remove_edge(u, v)
        componentes = list(nx.connected_components(G_temp))
        left,right=list(componentes[0]),list(componentes[1])
        if len(left)>1 and len(right)>1:
            (a,b)=bridge
            if len(left) <= len(right):
                all.append([a, b, left, right])
            else:
                all.append([b, a, right, left])
    return all
#-------------------------------------------------------------------------------
def dihedral_rotation(moleculein, bridgelist, ibridge, qdeg):
    sua=bridgelist[ibridge][0]
    nua=bridgelist[ibridge][1]
    lista=bridgelist[ibridge][2]
    vec=(moleculein[sua].position - moleculein[nua].position)
    vet=(moleculein[sua].position + moleculein[nua].position)/2.0
    rodriguesrm=rodrigues_rotation_matrix(vec, qdeg)
    for ii in range(len(moleculein)):
        if ii in lista:
            vri = np.matmul(rodriguesrm, moleculein[ii].position - vet)
            moleculein[ii].position=vri + vet
    return moleculein
#-------------------------------------------------------------------------------
def check_connectivity(atoms, adjmatrix_ref):
    adjmatrix_x=adjacency_matrix(atoms)
    return ( np.array_equiv(adjmatrix_x,adjmatrix_ref) or np.array_equal(adjmatrix_x,adjmatrix_ref) )
#-------------------------------------------------------------------------------
def rattle(moleculeseed, bridgelist, adjmatrix_ref, qdegamp=180.0):
    nbridges=len(bridgelist)
    moleculeout=moleculeseed.copy()
    for ibridge in range(nbridges):
        fall = True
        while fall:
            qdeg=random.randint(-int(qdegamp),int(qdegamp))
            dihedral_rotation(moleculeout, bridgelist, ibridge, qdeg)
            fall = False if ( check_connectivity(moleculeout, adjmatrix_ref) ) else True
    return moleculeout
#-------------------------------------------------------------------------------
def make_random_rotamers(moleculeseed, number, bridgelist, adjmatrix_ref):
    qdegamp=180
    id='seed00_'+str(1).zfill(ndigit)
    #print("\nBuild guest rotamer: %s (Initial seed as reference)" %(id))
    moleculetmp=moleculeseed.copy()
    moleculetmp.info['i']=id
    moleculeout=[moleculetmp]
    for key in range(number-1):
        id='random_'+str(int(key+2)).zfill(ndigit)
        #print("Build guest rotamer: %s" %(id))
        moleculetmp=rattle(moleculeseed, bridgelist, adjmatrix_ref, qdegamp)
        moleculetmp.info['i']=id
        moleculetmp.info['e']=0.0
        moleculeout.extend([moleculetmp])
    return moleculeout
#-------------------------------------------------------------------------------
def make_mutant_rotamers(rotamerlist, bridgelist, adjmatrix_ref):
    """
    Creates mutant rotamers by accumulating rotations around the 2 most symmetric bridges.
    
    Strategy:
    - Start from input rotamer
    - Apply random rotation to bridge 1
    - If valid: keep it and continue
    - If invalid: try another angle until finding a valid one
    - Repeat for bridge 2, starting from the state after bridge 1
    """
    qdegamp = 180
    max_attempts = 25
    
    # Sort bridges by symmetry (smallest difference in fragment sizes)
    lista = [[i, np.abs(len(xa[2]) - len(xa[3]))] for i, xa in enumerate(bridgelist)]
    liste = sorted(lista, key=lambda x: float(x[1]))
    indexes = [x[0] for x in liste]
    
    moleculeout = []
    
    for i, imol in enumerate(rotamerlist):
        # Start with the input rotamer (this will accumulate rotations)
        tmp = imol.copy()
        
        # Rotate around the 2 most symmetric bridges (accumulative)
        for bridge_idx, index in enumerate(indexes[:2]):
            success = False
            attempts = 0
            
            while not success and attempts < max_attempts:
                # Try a rotation starting from current accumulated state
                tmp_attempt = tmp.copy()  # Copy current state (with previous rotations)
                
                # Generate random rotation angle
                qdeg = random.randint(-int(qdegamp), int(qdegamp))
                
                # Apply rotation
                dihedral_rotation(tmp_attempt, bridgelist, index, qdeg)
                
                # Check if connectivity is preserved
                if check_connectivity(tmp_attempt, adjmatrix_ref):
                    # SUCCESS: Keep this rotation and continue accumulating
                    tmp = tmp_attempt  # Update to new valid state
                    success = True
                    print(f"  Mutant {i+1}/{len(rotamerlist)} - Bridge {bridge_idx+1}/2: {qdeg:+4d}° applied ✓", 
                          end='\r', flush=True)
                else:
                    # FAILED: Discard tmp_attempt, try another angle
                    # tmp remains unchanged (keeps previous valid rotations)
                    pass
                
                attempts += 1
            
            if not success:
                # Clear the progress line before printing warning
                print(" " * 80, end='\r', flush=True)
                print(f"WARNING: Mutant {i+1} - Could not rotate bridge {index} after {max_attempts} attempts")
        
        # Assign new ID and add to output
        id_name = 'mutant_' + str(i + 1).zfill(ndigit)
        tmp.info['i'] = id_name
        tmp.info['e'] = 0.0
        moleculeout.append(tmp)
        
        # Clear the progress line
        print(" " * 80, end='\r', flush=True)
        print(f"Mutant {i+1}/{len(rotamerlist)}: {id_name} created", end='\r', flush=True)
    
    print()  # New line at the end
    return moleculeout
#-------------------------------------------------------------------------------
def align_bond_to_z(atoms, i, j):
    """Rota la molécula para alinear el enlace i-j con el eje z."""
    vec=(atoms[j].position - atoms[i].position)
    vet=(atoms[j].position + atoms[i].position)/2.0
    gv1=vec/np.linalg.norm(vec)
    moleculeout=atoms.copy()
    if ( np.cross(gv1, zeta) == zero).all():
        return moleculeout
    m1 = np.array([gv1[1], -gv1[0], 0.0])
    m2 = np.cross(gv1, m1)
    tmatrix = np.array([m1, m2, gv1])
    moleculeout.set_positions(np.dot(atoms.get_positions() - vet, tmatrix.T))
    return moleculeout
#-------------------------------------------------------------------------------
def crossover_rotamers(mola, molb, bridgelist, adjmatrix_ref):
    lista=[[i, np.abs(len(xa[2])-len(xa[3]))] for i,xa in enumerate(bridgelist)]
    liste = sorted(lista, key=lambda x: float(x[1]))
    indexes=[x[0] for x in liste]
    moleculeout=[]
    for index in indexes:
        i=bridgelist[index][0]
        j=bridgelist[index][1]
        aliga=align_bond_to_z(mola, i, j)
        aligb=align_bond_to_z(molb, i, j)
        left=bridgelist[index][2]
        right=bridgelist[index][3]
        for angle in range(0, 360, 5):
            var=aligb.copy()
            rotate_vector_angle_deg(var, zeta, angle)
            hijo=aliga.copy()
            for ii in right: hijo[ii].position=var[ii].position
            test=check_connectivity(hijo, adjmatrix_ref)
            if test:
                hijo.info['e']=float(0.0)
                hijo.info['i']='pre_child'+str(angle).zfill(4)
                return hijo
    if test is False: return False    
#-------------------------------------------------------------------------------
def make_crossover_rotamers(papy, mamy, bridgelist, adjmatrix_ref):
    moleculeout=[]
    total_molecules=len(papy)
    for imol in range(total_molecules):
         ichildren=crossover_rotamers(papy[imol],mamy[imol],bridgelist, adjmatrix_ref)
         if ichildren: moleculeout.extend([ichildren])
    rename(moleculeout, 'mating', ndigit)
    return moleculeout
#-------------------------------------------------------------------------------    
paracetamol = """20
0.0    Paracetamol
O       3.809521986      0.374653824      0.252342818
O      -3.805446140     -0.243326005     -0.099559428
N      -1.632898387     -0.594228692     -0.545580069
C      -0.241671281     -0.378149990     -0.367812893
C       0.566313683     -1.368109043      0.196966445
C       0.341115148      0.832526503     -0.735048347
C       1.921376702     -1.138640088      0.417436324
C       1.693807747      1.064201659     -0.519474821
C       2.487369463      0.083144573      0.062940409
C      -2.645511371      0.069354037      0.104899970
C      -2.251986590      1.185098749      1.044006465
H       0.130501657     -2.316305889      0.487180748
H      -0.266652746      1.597483509     -1.198729534
H      -1.948674878     -1.388556402     -1.080481626
H       2.528004407     -1.919697234      0.862317940
H       2.144129035      2.007029945     -0.799530083
H      -2.005526715      2.084189332      0.469843584
H      -1.376464160      0.922879514      1.641131601
H      -3.101528200      1.404048623      1.687742471
H       4.244131237     -0.379477896      0.658258486
"""
#-------------------------------------------------------------------------------    
def ejemplo():
    from io import StringIO
    from ase.io import read
    from aegon.libutils import adjacency_matrix, writexyzs, sort_by_energy
    from aegon.libroulette import get_roulette_wheel_selection
    from aegon.libcalc_ani import calculator_anix_all
    from aegon.libdiscusr import comparator_usr_serial
    nmatings=4
    nmutants=4
    tolsim=0.95
    xyz_file = StringIO(paracetamol)
    atoms = read(xyz_file, format='xyz')
    atoms.info['e']=0.0
    atoms.info['i']='Paracetamol'
    adjmatrix = adjacency_matrix(atoms)
    bridgelist = get_bridge_left_right(adjmatrix)
    moleculeout=[]
    for i in range(len(bridgelist)):
        for qdeg in range(0, 360, 5):
            tmp=atoms.copy()
            dihedral_rotation(tmp, bridgelist, i, qdeg)
            moleculeout.extend([tmp])
    xmol=make_random_rotamers(atoms, 4, bridgelist, adjmatrix)
    writexyzs(xmol, 'rotgen0.xyz')
    xopt=calculator_anix_all(xmol)
    xopt_sort=sort_by_energy(xopt, 1)
    xopt_sort=comparator_usr_serial(xopt_sort, tolsim)
    for ix in xopt_sort: print("%s %.6f %.6f" %(ix.info['i'], ix.info['e'], ix.info['e']-xopt_sort[0].info['e']))
    print('GENERACION %d' %(1))
    list_p=get_roulette_wheel_selection(xopt_sort, nmatings)
    list_m=get_roulette_wheel_selection(xopt_sort, nmatings)
    atoms_list_out=make_crossover_rotamers(list_p, list_m, bridgelist, adjmatrix)
    atoms_list_mut=make_mutant_rotamers(xopt_sort[:nmutants], bridgelist, adjmatrix)
    generation_opt=calculator_anix_all(atoms_list_out+atoms_list_mut, opt='ani1ccx', preclist=[1E-03])
    xopt_sort=sort_by_energy(xopt_sort+generation_opt, 1)
    xopt_sort=comparator_usr_serial(xopt_sort, tolsim)
    for ix in xopt_sort[:]: print("%s %.6f %.6f" %(ix.info['i'], ix.info['e'], ix.info['e']-xopt_sort[0].info['e']))
    writexyzs(xopt_sort, 'rotgen1.xyz')
#ejemplo()
