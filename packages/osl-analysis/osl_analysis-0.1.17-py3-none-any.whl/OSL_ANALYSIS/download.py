# download.py
import numpy as np
from .E_values import F_ph_array, longitud_array, Sigma1_array, Sigma2_array, Sigma3_array, Fuente_Luz_array, pf1_v, pf2_v, pf3_v
import os

def run_download():
    # Check that F_ph_array is defined
    if F_ph_array is None:
        raise ValueError("F_ph_array is not defined. Run modulo1 first")
    if longitud_array is None or Sigma1_array is None:
        raise ValueError("Data arrays not defined. Run modulo1 first")

    print("\n" + "="*50)
    print("SAVING DATA TO FILES")
    print("="*50)

    num_archivos = len(F_ph_array)
    print(f"{num_archivos} file(s) will be created")
    
    # Use the real data arrays from modulo1
    # longitud_array, Sigma1_array, Sigma2_array, Sigma3_array, Fuente_Luz_array are already defined
    
    pf1_v, pf2_v, pf3_v = [], [], []  # But use the real ones if available
    if pf1_v is not None:
        pf1_v = pf1_v
        pf2_v = pf2_v
        pf3_v = pf3_v
    else:
        # Fallback, but should not happen
        pf1_v = [0] * len(F_ph_array)
        pf2_v = [0] * len(F_ph_array)
        pf3_v = [0] * len(F_ph_array)
    
    # Save each file
    for fph_valor in F_ph_array:
        file_name = f"photo_stimulation_Fph_{fph_valor:.1f}nm.txt"
    
        # Combine arrays into a single matrix
        data_fph = np.column_stack((
            longitud_array,
            Sigma1_array,
            Sigma2_array,
            Sigma3_array,
            Fuente_Luz_array
        ))
    
        np.savetxt(file_name, data_fph,
                   delimiter='\t',
                   fmt=['%.2f', '%.6e', '%.6e', '%.6e', '%.6f'],
                   header='LONG\tSIGMA1\tSIGMA2\tSIGMA3\tSOURCE',
                   comments='')
    
        print(f"✅ File created: {file_name}")
    
        # Save example sums
        pf1_v.append(Sigma1_array.sum())
        pf2_v.append(Sigma2_array.sum())
        pf3_v.append(Sigma3_array.sum())
    
    # Create summary file if there is more than one F_ph
    if len(F_ph_array) > 1:
        summary_file = "summary_parameters.txt"
        summary_data = np.column_stack((F_ph_array, pf1_v, pf2_v, pf3_v))
        np.savetxt(summary_file, summary_data,
                   delimiter='\t',
                   fmt=['%.2f', '%.6e', '%.6e', '%.6e'],
                   header='F_ph\tpf1\tpf2\tpf3',
                   comments='')
    
        print("\nParameter summary:")
        print("F_ph\tpf1\tpf2\tpf3")
        for i in range(len(F_ph_array)):
            print(f"{F_ph_array[i]:.2f}\t{pf1_v[i]:.6e}\t{pf2_v[i]:.6e}\t{pf3_v[i]:.6e}")
    
    # ======================================
    # Download files in Colab
    # ======================================
    try:
        from google.colab import files
        print("\nDOWNLOADING FILES IN COLAB...")
        for fph_valor in F_ph_array:
            file_name = f"photo_stimulation_Fph_{fph_valor:.1f}nm.txt"
            files.download(file_name)
            print(f"📥 Downloaded: {file_name}")
    
        if len(F_ph_array) > 1:
            files.download(summary_file)
            print(f"📥 Downloaded: {summary_file}")
    
    except ImportError:
        print("\n⚠️ Google Colab not found - files saved locally")
        print("Files created:")
        for fph_valor in F_ph_array:
            print(f" • photo_stimulation_Fph_{fph_valor:.1f}nm.txt")
        if len(F_ph_array) > 1:
            print(f" • {summary_file}")
    
    print("\nPROCESS COMPLETED")
    print("="*50)
