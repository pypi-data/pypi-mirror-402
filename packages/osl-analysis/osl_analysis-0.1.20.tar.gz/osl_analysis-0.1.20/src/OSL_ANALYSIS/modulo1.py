
import numpy as np
import pandas as pd

from scipy.integrate import odeint
import matplotlib.pyplot as plt
import warnings

import math
from scipy.optimize import curve_fit
from prettytable import PrettyTable

from .E_values import E1, E2, E3
from . import E_values

def main():
    warnings.filterwarnings("ignore")
# Numerical constants for the photostimulation model
a,g_,h,F_ph,sigma,I_ph = 0.0001,0.5,4.13566743E-15,470,5,1E3


# Request F_ph values from user
user_input = input("Enter F_ph values (in nm):\n" +
                  "  - For a single value: enter the number (e.g. 470)\n" +
                  "  - For a range: enter start,end,step separated by commas (e.g. 400,700,10)\n" +
                  "  - For multiple specific values: enter values separated by hyphens (e.g. 400-500-700)\n" +
                  ">> ")

# Process user input
if '-' in user_input:
    # Multiple values separated by hyphens
    F_ph_array = np.array([float(x.strip()) for x in user_input.split('-')])
elif ',' in user_input:
    # Separate by commas
    valores = [x.strip() for x in user_input.split(',')]

    if len(valores) == 3:
        # Check if it's a valid range
        try:
            inicio = float(valores[0])
            fin = float(valores[1])
            paso = float(valores[2])
            # If end > start and step > 0, it's a range
            if fin > inicio and paso > 0:
                F_ph_array = np.arange(inicio, fin + paso, paso)
            else:
                # Otherwise, they are specific values
                F_ph_array = np.array([float(x) for x in valores])
        except ValueError:
            # If there's a conversion error, they are specific values
            F_ph_array = np.array([float(x) for x in valores])
    else:
        # Multiple specific values (though hyphens should be used)
        F_ph_array = np.array([float(x) for x in valores])
else:
    # Single value
    F_ph_array = np.array([float(user_input.strip())])

print(f"F_ph_array: {F_ph_array}")

E_values.F_ph_array = F_ph_array

pf1_v=[]
pf2_v=[]
pf3_v=[]

for j in range(len(F_ph_array)): # Iterate over F_ph_array
 F_ph_scalar = F_ph_array[j] # Get scalar value for current iteration

 longitud=[]
 Frecuencia=[]
 Sigma1=[]
 Sigma2=[]
 Sigma3=[]
 Fuente_Luz=[]

 pf1_=0
 pf2_=0
 pf3_=0

 for i in range(1, 1011): # Start range from 1 to avoid index out of bounds
    longitud_i = 100+i # Use scalar variable
    Frecuencia_i = ((300000*1000)/((longitud_i*0.000000001))) # Use scalar variable
    # Use np.power for element-wise power
    Sigma1_i = a*math.sqrt(E1)*(((h*Frecuencia_i-E1)**(3/2))/(h*Frecuencia_i*(h*Frecuencia_i-g_*E1)**(2)))
    Sigma2_i = a*math.sqrt(E2)*(((h*Frecuencia_i-E2)**(3/2))/(h*Frecuencia_i*(h*Frecuencia_i-g_*E2)**(2)))
    Sigma3_i = a*math.sqrt(E3)*(((h*Frecuencia_i-E3)**(3/2))/(h*Frecuencia_i*(h*Frecuencia_i-g_*E3)**(2)))

    Fuente_Luz_i = np.exp(-((longitud_i-F_ph_scalar)**(2))/(2*sigma**2)) # Use np.exp and scalar F_ph

    longitud.append(longitud_i)
    Frecuencia.append(Frecuencia_i)
    Sigma1.append(Sigma1_i)
    Sigma2.append(Sigma2_i)
    Sigma3.append(Sigma3_i)
    Fuente_Luz.append(Fuente_Luz_i)


    if h*Frecuencia_i>E1:
      pf1_= pf1_+Sigma1_i*Fuente_Luz_i*I_ph
    if h*Frecuencia_i>E2:
      pf2_= pf2_+Sigma2_i*Fuente_Luz_i*I_ph
    if h*Frecuencia_i>E3:
      pf3_= pf3_+Sigma3_i*Fuente_Luz_i*I_ph

 pf1_v.append(pf1_)
 pf2_v.append(pf2_)
 pf3_v.append(pf3_)

# Convert lists to numpy arrays to avoid error with .real
longitud_array = np.array(longitud)
Sigma1_array = np.array(Sigma1)
Sigma2_array = np.array(Sigma2)
Sigma3_array = np.array(Sigma3)
Fuente_Luz_array = np.array(Fuente_Luz)

# Plot data for each energy value
plt.figure(figsize=(10, 5))

# Graph the data
#plt.ylim(0, 5e-7)
plt.plot(longitud_array, Sigma1_array, 'b--', linewidth=2, label='$^{I}σ_{0}(λ)$')
plt.plot(longitud_array, Sigma2_array, 'g--', linewidth=2, label='$^{II}σ_{0}(λ)$')
plt.plot(longitud_array, Sigma3_array, 'r--', linewidth=2, label='$^{III}σ_{0}(λ)$')
leg = plt.legend(loc='upper left')
plt.ylabel('σ$_{0}$')
plt.xlabel('λ [nm]')

ax2 = plt.twinx()
ax2.plot(longitud_array, Fuente_Luz_array, 'y', label='ϕ(λ)')
ax2.legend()
ax2.set_ylim(0,1.2)
ax2.set_ylabel('ϕ(λ)')

# Save arrays to global for download
E_values.longitud_array = longitud_array
E_values.Sigma1_array = Sigma1_array
E_values.Sigma2_array = Sigma2_array
E_values.Sigma3_array = Sigma3_array
E_values.Fuente_Luz_array = Fuente_Luz_array
E_values.pf1_v = pf1_v
E_values.pf2_v = pf2_v
E_values.pf3_v = pf3_v

main()