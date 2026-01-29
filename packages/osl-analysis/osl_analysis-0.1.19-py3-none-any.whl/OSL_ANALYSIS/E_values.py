E1 = None
E2 = None
E3 = None
F_ph_array = None
longitud_array = None
Sigma1_array = None
Sigma2_array = None
Sigma3_array = None
Fuente_Luz_array = None
pf1_v = None
pf2_v = None
pf3_v = None
n_1 = None
n_2 = None
n_3 = None
nc_ = None
nv_ = None
m_ = None

def set_values():
    global E1, E2, E3
    E1 = float(input("Ingrese E1: "))
    E2 = float(input("Ingrese E2: "))
    E3 = float(input("Ingrese E3: "))

def set_test_values(e1, e2, e3):
    global E1, E2, E3
    E1, E2, E3 = e1, e2, e3
