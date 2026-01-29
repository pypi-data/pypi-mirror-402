
import numpy as np
from scipy.integrate import odeint
import pandas as pd
from IPython.display import display
import matplotlib.pyplot as plt

from .E_values import E1, E2, E3, n_1, n_2, n_3, nc_, nv_, m_

# Physical constants
kB = 8.617333262e-5  # Boltzmann constant in eV/K

# Numerical parameters for the TTOR model
M, N = 1.5e7, 1e7
An, Am = 1e-8, 1e-6
s = 2e12

# Other parameters
f = 0
AmR = 5e-4
#An = Am * 0.01
hr = 0

# Initial conditions (from modulo2 if available)
n01 = n_1 if n_1 is not None else 0
n02 = n_2 if n_2 is not None else 0
n03 = n_3 if n_3 is not None else 0
nc0 = nc_ if nc_ is not None else 0
nv0 = nv_ if nv_ is not None else 0
m0  = m_ if m_ is not None else 0

# Initial conditions vector
y0 = [n01, n02, n03, nc0, m0, nv0]

# Request TE values from user
print("="*50)
print("EQUILIBRIUM TEMPERATURE (TE) INPUT")
print("="*50)
te_input = "300"  # Valor por defecto
te_input = input("Enter TE values (in °C):\n" +
                  "  - For a single value: enter the number (e.g. 300)\n" +
                  "  - For a range: enter start,end,step separated by commas (e.g. 300,400,25)\n" +
                  "  - For multiple specific values: enter values separated by hyphens (e.g. 300-350-400)\n" +
                  ">> ")

# Process user input
if '-' in te_input:
    # Multiple values separated by hyphens
    te_values = np.array([float(x.strip()) for x in te_input.split('-')])
elif ',' in te_input:
    # Separate by commas
    valores = [x.strip() for x in te_input.split(',')]
    
    if len(valores) == 3:
        # Check if it's a valid range
        try:
            inicio = float(valores[0])
            fin = float(valores[1])
            paso = float(valores[2])
            # If end > start and step > 0, it's a range
            if fin > inicio and paso > 0:
                te_values = np.arange(inicio, fin + paso, paso)
            else:
                # Otherwise, they are specific values
                te_values = np.array([float(x) for x in valores])
        except ValueError:
            # If there's a conversion error, they are specific values
            te_values = np.array([float(x) for x in valores])
    else:
        # Multiple specific values (though hyphens should be used)
        te_values = np.array([float(x) for x in valores])
else:
    # Single value
    te_values = np.array([float(te_input.strip())])

print(f"\nTE values to process: {te_values}")
print(f"Number of temperatures: {len(te_values)}")

def deriv(y, t, TE):
    n1, n2, n3, nc, m, nv = y
    temp = 273.15 + TE + hr * t  # Temperature in K

    # Optical probability
    pf1 = 0
    pf2 = 0
    pf3 = 0

    # Probability calculation
    p1 = s * np.exp(-E1 / (kB * temp))
    p2 = s * np.exp(-E2 / (kB * temp))
    p3 = s * np.exp(-E3 / (kB * temp))

    # System of differential equations
    dmdt = -m * Am * nc + AmR * (M - m) * nv
    dndt1 = -pf1 * n1 - n1 * p1 + nc * An * (N - n1)
    dndt2 = -pf2 * n2 - n2 * p2 + nc * An * (N - n2)
    dndt3 = -pf3 * n3 - n3 * p3 + nc * An * (N - n3)
    dncdt = f - dndt1 - dndt2 - dndt3 - Am * m * nc
    dnvdt = f - AmR * (M - m) * nv

    return [dndt1, dndt2, dndt3, dncdt, dmdt, dnvdt]

def solve_ode(TE):
    t_max = 10  # Maximum time (seconds)
    steps = 100  # Increased for better resolution
    t = np.linspace(0, t_max, steps)

    solution = odeint(deriv, y0, t, args=(TE,))
    return t, solution.T

# Create a figure for all plots if there are multiple temperatures
if len(te_values) > 1:
    plt.figure(figsize=(15, 10))
    
    # Generate distinct colors for each variable
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    labels = ['n₁', 'n₂', 'n₃', 'nc', 'nv']

    # Create subplots for each temperature
    n_temps = len(te_values)
    n_rows = (n_temps + 2) // 3  # Calculate required number of rows
    n_cols = min(3, n_temps)
    
    for i, TE in enumerate(te_values):
        # Create the subplot in the main figure
        plt.subplot(n_rows, n_cols, i+1)

        # Solve ODE and plot
        t, (n1, n2, n3, nc, m, nv) = solve_ode(TE)
        solutions = [n1, n2, n3, nc, nv, m]

        for sol, color, label in zip(solutions, colors, labels):
            plt.plot(t, sol, color=color, label=label, linewidth=1.5)

        # Configure the plot
        plt.title(f"TE = {TE}ºC")
        plt.xlabel("Time (s)")
        plt.ylabel("Concentration (cm−3)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)

    # Adjust the layout
    plt.tight_layout()
    plt.show()

# Process each temperature individually
for TE in te_values:
    print(f"\n{'='*50}")
    print(f"PROCESSING TE = {TE}°C")
    print(f"{'='*50}")
    
    # Create a new figure with 3 subplots for each temperature
    fig = plt.figure(figsize=(18, 6))  # Wider size to accommodate 3 subplots

    # Solve ODE
    t, (n1, n2, n3, nc, m, nv) = solve_ode(TE)
    
    # Subplot 1: Trap concentrations
    plt.subplot(1, 3, 1)
    plt.plot(t, n1, 'b--', linewidth=2, label='n$_1$(t)')
    plt.plot(t, n2, 'g--', linewidth=2, label='n$_2$(t)')
    plt.plot(t, n3, 'r--', linewidth=2, label='n$_3$(t)')
    plt.plot(t, nc, 'r', linewidth=2, label='n$_c$(t)')
    plt.plot(t, nv*100, 'magenta', linewidth=2, label='n$_v$(t)×100')
    
    leg = plt.legend(loc='best')
    leg.get_frame().set_linewidth(0.0)
    plt.ylabel('Filled traps [cm$^{-3}$]')
    plt.xlim(0, 100)
    plt.title(f'Variation of trap concentrations\n(TE = {TE}°C)')
    plt.xlabel(r'Time [s]')
    plt.grid(True, alpha=0.3)

    # Subplot 2: dmdt
    plt.subplot(1, 3, 2)
    dmdt_plot = m * Am * nc
    plt.plot(t, dmdt_plot, 'r', linewidth=2, label='dmdt = m·Am·nc')
    plt.ylabel('dmdt [a.u.]')
    plt.xlabel(r'Time [s]')
    plt.xlim(0, 100)
    plt.title(f'TL Glow Curve TTOR Model\n(TE = {TE}°C)')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best')

    # Subplot 3: Charge neutrality
    plt.subplot(1, 3, 3)
    a_val = (nc + n1 + n2 + n3) / (m + nv)
    plt.plot(t, a_val, 'r', linewidth=2, label='n = (n1+n2+n3+nc)/(nv+m)')
    plt.ylabel('n [a.u.]')
    plt.xlabel('Time [s]')
    plt.title(f'Evaluation of charge neutrality\n(TE = {TE}°C)')
    plt.ylim(0, 2)
    plt.xlim(0, 10)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best')

    # Adjust the layout
    plt.tight_layout()
    
    # Save the figure as PNG
    nombre_png = f'calent_{TE}C.png'
    plt.savefig(nombre_png, dpi=300, bbox_inches='tight')
    print(f"✅ Figure saved: {nombre_png}")
    
    plt.show()
    
    # Save data in text file
    dmdt = m * Am * nc 
    data = np.column_stack((t, dmdt, n1, n2, n3, nc, nv, m))
    
    # Specify the path and file name where you want to save the data
    archivo_txt = f"calent_{TE}C.txt"
    
    # Save all data in the text file
    np.savetxt(archivo_txt, data, delimiter='\t', 
               header='Time [s]\tdmdt(a.u.)\tn1(t) [cm^-3]\tn2(t) [cm^-3]\tn3(t) [cm^-3]\tnc(t) [cm^-3]\tnv(t) [cm^-3]\tm[cm^-3]', 
               comments='',
               fmt=['%.6f', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e'])
    
    print(f"✅ Data saved: {archivo_txt}")
    
    # Download file (if in Google Colab)
    try:
        from google.colab import files
        files.download(archivo_txt)
        print(f"📊 File downloaded: {archivo_txt}")
    except ImportError:
        print("ℹ️  Google Colab not found - file saved locally")

print(f"\n{'='*50}")
print(f"PROCESS COMPLETED - Total temperatures: {len(te_values)}")
print(f"{'='*50}")