
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

n01= 0
n02= 0
n03= 0
nc0= 0
nv0= 0

# Charge neutrality conditions
m0 = 0
# Initial conditions vector
y0 = [n01, n02, n03, nc0, m0, nv0]


# Numerical parameters for the TTOR model
M,N, An, Am, s = 1.5e7, 1e7, 1e-8, 1e-6, 2e12


TE=25

f=  100
AmR= 5e-4
An=Am*0.01
hr=  0


# Generate time vector using a for loop
num_puntos = 100

intervalo_tiempo = 1  # 1 second
t = np.zeros(num_puntos)
for i in range(num_puntos):
    t[i] = i * intervalo_tiempo

    kB = 8.617e-5
    #TE=25


  # Initial conditions vector
# y0 = [n01, n02, n03, nc0, m0, nv0] # This line is redundant as y0 is defined above
  # Differential equations for the TTOR model
def deriv(y, t):
    n1, n2, n3, nc, m, nv = y
    pf1 = 0
    pf2 = 0
    pf3 = 0

    # Thermal probability
    p1 = s * np.exp(-E1 / (kB * (273.15 + TE +  hr * t)))
    p2 = s * np.exp(-E2 / (kB * (273.15 + TE +  hr * t)))
    p3 = s * np.exp(-E3 / (kB * (273.15 + TE +  hr * t)))



    dmdt = -m * Am * nc + AmR * (M-m) * nv
    dndt1 = -n1 * pf1 - n1 * p1 + nc * An *  (N - n1)
    dndt2 = -n2 * pf2 - n2 * p2 + nc * An *  (N - n2)
    dndt3 = -n3 * pf3 - n3 * p3 + nc * An  * (N - n3)
    dncdt = f - dndt1 - dndt2 - dndt3 - Am * m * nc
    dnvdt = f  - AmR * (M-m) * nv


    return dndt1, dndt2, dndt3, dncdt, dmdt, dnvdt

# Move the odeint call outside the function definition
ret = odeint(deriv, y0, t)
# Unpack the results into variables accessible for plotting
n1, n2, n3,nc, m, nv = ret.T

# Save final values for use in modulo3 and modulo4
E_values.n_1 = n1[-1]
E_values.n_2 = n2[-1]
E_values.n_3 = n3[-1]
E_values.nc_ = nc[-1]
E_values.nv_ = nv[-1]
E_values.m_ = m[-1]


# Plot data for each energy value
plt.figure(figsize=(12, 5))


# Plot the data
plt.subplot(1, 3, 1)
plt.plot(t, n1, 'b--', linewidth=2, label='n$_1$(t)')
plt.plot(t, n2, 'g--', linewidth=2, label='n$_2$(t)')
plt.plot(t, n3, 'r--', linewidth=2, label='n$_3$(t)')

plt.plot(t, nc, 'r', linewidth=2, label='n$_c$(t)')
plt.plot(t, nv*100, 'magenta', linewidth=2, label='n$_v$(t)')

leg = plt.legend()
leg.get_frame().set_linewidth(0.0)
plt.ylabel('Filled traps [cm$^{-3}$]')
#plt.ylim(0, 1e4)
plt.xlim(0, 100)
plt.title('Variation of trap concentrations')
plt.xlabel(r'Time [s]')

plt.subplot(1, 3, 2)
# Calculate dmdt here using the unpacked variables
dmdt = m * Am * nc
plt.plot(t, dmdt, 'r', linewidth=2, label='dmdt=m.Am.nc')
plt.ylabel('dmdt [a.u.]')
plt.xlabel(r'Time [s]')
#plt.ylim(0, 20)
plt.xlim(0, 100)
plt.title('OSL Glow Curve TTOR model')
plt.tight_layout()

plt.subplot(1, 3, 3)
# Calculate 'a' here using the unpacked variables

a = (nc + n1 + n2 + n3) / (m + nv)

# Ignore the first value (index 0)
#a[0] = a[1]  # Or you can use interpolation, or just remove it

plt.plot(t, a, 'r', linewidth=2, label='n  =  (n1 + n2 + n3 + nc) / (nv + m)')
plt.ylabel('n [a.u.]')
plt.xlabel('Time [s]')
plt.title('Evaluation of charge neutrality')
plt.ylim(0, 2)
plt.xlim(0, 10)
plt.tight_layout()


# Save data in .txt format
# Open them in Origin

# Assume you have multiple datasets
data = np.column_stack((t,dmdt, n1, n2, n3, nc, nv, m))

# Especifica la ruta y el nombre de archivo donde deseas guardar los datos
archivo_txt = "Irradiacion.txt"

# Guarda todos los datos en el archivo TXT
np.savetxt(archivo_txt, data, delimiter='\t', header='Time [s]\tdmdt [u.a.]\tn1(t) [cm^-3]\tn2(t) [cm^-3]\tn3(t) [cm^-3]\tnc(t) [cm^-3]\tnv(t) [cm^-3]\tm [cm^-3]', comments='')

# Show the plots
plt.show()