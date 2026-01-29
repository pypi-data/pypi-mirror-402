
import numpy as np
from scipy.integrate import odeint
import pandas as pd
from IPython.display import display
import matplotlib.pyplot as plt

from .E_values import E1, E2, E3, n_1, n_2, n_3, nc_, nv_, m_

# =============================================================================
# Fixed model parameters
# =============================================================================
kB = 8.617333262e-5
M, N = 1.5e7, 1e7
An, Am = 1e-8, 1e-6
s = 2e12

f = 0
AmR = 5e-4
hr = 0

# =============================================================================
# Temperature and time configuration (MODIFIED FOR USER INPUT)
# =============================================================================
print("="*50)
print("EQUILIBRIUM TEMPERATURE (TE) INPUT")
print("="*50)
te_input = "300"  # Valor por defecto
te_input = input("Enter TE values (in °C):\n" +
                  "  - For a single value: enter the number (e.g. 300)\n" +
                  "  - For a range: enter start,end,step separated by commas (e.g. 175,325,25)\n" +
                  "  - For multiple specific values: enter values separated by hyphens (e.g. 175-200-250-300)\n" +
                  ">> ")

# Process user input
if '-' in te_input:
    # Multiple values separated by hyphens
    TE_values = np.array([float(x.strip()) for x in te_input.split('-')])
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
                TE_values = np.arange(inicio, fin + paso, paso)
            else:
                # Otherwise, they are specific values
                TE_values = np.array([float(x) for x in valores])
        except ValueError:
            # If there's a conversion error, they are specific values
            TE_values = np.array([float(x) for x in valores])
    else:
        # Multiple specific values (though hyphens should be used)
        TE_values = np.array([float(x) for x in valores])
else:
    # Single value
    TE_values = np.array([float(te_input.strip())])

print(f"\nTE values to process: {TE_values}")
print(f"Number of temperatures: {len(TE_values)}")

# =============================================================================
# Time configuration
# =============================================================================
t_max = 200
t_points = 200
t = np.linspace(0, t_max, t_points)

# =============================================================================
# Results storage
# =============================================================================
results = {
    'lambda': [],
    'TE': [],
    't': [],
    'pf1': [],
    'pf2': [],
    'pf3': [],
    'n1': [],
    'n2': [],
    'n3': [],
    'nc': [],
    'nv': [],
    'm': []
}

# =============================================================================
# Initial conditions (from modulo2 if available)
# =============================================================================
n_1_init = n_1 if n_1 is not None else 0
n_2_init = n_2 if n_2 is not None else 0
n_3_init = n_3 if n_3 is not None else 0
nc_init = nc_ if nc_ is not None else 0
nv_init = nv_ if nv_ is not None else 0
m_init = m_ if m_ is not None else 0

# =============================================================================
# ODE system function
# =============================================================================
def deriv(y, t, pf1, pf2, pf3, TE):
    n1, n2, n3, nc, m, nv = y
    temp = 273.15 + TE
    p1 = s * np.exp(-E1 / (kB * temp))
    p2 = s * np.exp(-E2 / (kB * temp))
    p3 = s * np.exp(-E3 / (kB * temp))

    dmdt = -m * Am * nc + AmR * (M - m) * nv
    dndt1 = -pf1 * n1 - n1 * p1 + nc * An * (N - n1)
    dndt2 = -pf2 * n2 - n2 * p2 + nc * An * (N - n2)
    dndt3 = -pf3 * n3 - n3 * p3 + nc * An * (N - n3)
    dncdt = f - dndt1 - dndt2 - dndt3 - Am * m * nc
    dnvdt = f - AmR * (M - m) * nv

    return [dndt1, dndt2, dndt3, dncdt, dmdt, dnvdt]

# =============================================================================
# Corrected main loop
# =============================================================================
# Make sure pf1_v, pf2_v, pf3_v and F_ph_array have the same length
J = min(len(pf1_v), len(pf2_v), len(pf3_v), len(F_ph_array))

for j in range(J):  # Use J instead of len(pf1_v)
    current_pf1 = pf1_v[j]
    current_pf2 = pf2_v[j]
    current_pf3 = pf3_v[j]
    current_lambda = F_ph_array[j]  # Get the corresponding wavelength

    for TE in TE_values:
        print(f"\n{'='*60}")
        print(f"PROCESSING λ = {current_lambda:.1f} nm, TE = {TE}°C")
        print(f"{'='*60}")
        
        y0 = [n_1_init, n_2_init, n_3_init, nc_init, m_init, nv_init]
        solution = odeint(deriv, y0, t, args=(current_pf1, current_pf2, current_pf3, TE))
        n1, n2, n3, nc, m, nv = solution.T

        # =============================================================================
        # CREATION OF THE THREE PLOTS
        # =============================================================================
        # Create a new figure with 3 subplots
        fig = plt.figure(figsize=(18, 6))
        fig.suptitle(f'λ = {current_lambda:.1f} nm, TE = {TE}ºC', fontsize=16, y=1.02)
        
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
        plt.title('Variation of trap concentrations')
        plt.xlabel(r'Time [s]')
        plt.grid(True, alpha=0.3)

        # Subplot 2: dmdt
        plt.subplot(1, 3, 2)
        dmdt_plot = m * Am * nc
        plt.plot(t, dmdt_plot, 'r', linewidth=2, label='dmdt = m·Am·nc')
        plt.ylabel('dmdt [a.u.]')
        plt.xlabel(r'Time [s]')
        plt.xlim(0, 100)
        plt.title('TL Glow Curve TTOR model')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best')

        # Subplot 3: Charge neutrality
        plt.subplot(1, 3, 3)
        a_val = (nc + n1 + n2 + n3) / (m + nv)
        plt.plot(t, a_val, 'r', linewidth=2, label='n = (n1+n2+n3+nc)/(nv+m)')
        plt.ylabel('n [a.u.]')
        plt.xlabel('Time [s]')
        plt.title('Evaluation of charge neutrality')
        plt.ylim(0, 2)
        plt.xlim(0, 10)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best')

        # Adjust the layout
        plt.tight_layout()
        
        # Show the figure
        plt.show()
        
        # Save the figure as PNG
        nombre_png = f'lambda_{current_lambda:.1f}nm_TE_{TE}C.png'
        plt.savefig(nombre_png, dpi=300, bbox_inches='tight')
        print(f"✅ Figure saved: {nombre_png}")
        
        # Close the figure to free memory
        plt.close(fig)
        
        # Store results in the dictionary
        for k in range(len(t)):
            results['lambda'].append(current_lambda)
            results['TE'].append(TE)
            results['t'].append(t[k])
            results['pf1'].append(current_pf1)
            results['pf2'].append(current_pf2)
            results['pf3'].append(current_pf3)
            results['n1'].append(n1[k])
            results['n2'].append(n2[k])
            results['n3'].append(n3[k])
            results['nc'].append(nc[k])
            results['nv'].append(nv[k])
            results['m'].append(m[k])
        
        # Save data in text file for this combination
        dmdt_save = m * Am * nc 
        data = np.column_stack((t, dmdt_save, n1, n2, n3, nc, nv, m))
        
        archivo_txt = f"lambda_{current_lambda:.1f}nm_TE_{TE}C.txt"
        
        np.savetxt(archivo_txt, data, delimiter='\t',
                   header='Time [s]\tdmdt(a.u.)\tn1(t) [cm^-3]\tn2(t) [cm^-3]\tn3(t) [cm^-3]\tnc(t) [cm^-3]\tnv(t) [cm^-3]\tm[cm^-3]',
                   comments='',
                   fmt=['%.6f', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e', '%.6e'])
        
        print(f"✅ Data saved: {archivo_txt}")

# =============================================================================
# DataFrame creation
# =============================================================================
df_completo = pd.DataFrame(results)

# Verification
print("\n" + "="*50)
print("DATAFRAME SUMMARY")
print("="*50)
print(f"- Total points: {len(df_completo)}")
print(f"- Unique wavelengths: {len(df_completo['lambda'].unique())}")
print(f"- Unique temperatures: {sorted(df_completo['TE'].unique())}")
print(f"- Time range: {df_completo['t'].min()} to {df_completo['t'].max()} s")
print(f"- Time points per simulation: {len(t)}")

display(df_completo.head())