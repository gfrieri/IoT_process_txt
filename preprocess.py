#!/usr/bin/env python3
import os
import re
import argparse
from tqdm import tqdm
from dataclasses import dataclass
from io import TextIOWrapper
from time import sleep

# Regex de las Líneas
numbers = r"[+-]?(?:(?:\d+(?:\.\d*)?)|\.\d+)(?:[eE][+-]?\d+)?"

MY_STO = re.compile(f"\\[1frame_sync_impl.cc\\] \\d+My STO: ({numbers})") #?
DEF_LOG = re.compile(f"\\[frame_sync_impl.cc\\] \\d+ CFO estimate: ({numbers}), STO estimate: ({numbers}) snr est: ({numbers})") #?
MESSAGE = re.compile(f"rx msg: (.+:(\\d+))?") #?
CRC = re.compile(f"CRC (invalid|valid)")
OVERFLOW = re.compile(f"(\\d+) overflows") #?

# Clase de lineas csv dataclass
@dataclass
class Row:
    mensaje: str            # *
    numero: str             # *
    my_sto: str             # *
    sto: str                # *
    cfo: str                # *
    snr: str                # *
    crc_error: bool         # *
    overflow_count: int     # *

# Expresión regular para filtrar los archivos
FILE_REGEX = re.compile(r'^(\d+[mk])-(\d+m)-(\d+)[.]txt$', re.IGNORECASE)

def pre_process(infile: TextIOWrapper, outfile: TextIOWrapper, freq, distance, version):
    """
    Función de pre-procesado (aún sin implementación).
    
    Parámetros:
      infile   - Objeto de archivo de entrada
      outfile  - Objeto de archivo de salida
      freq     - Frecuencia de muestreo (primer grupo de la regex)
      distance - Distancia (segundo grupo de la regex)
      version  - Versión (tercer grupo de la regex)
    
    La función se encargará de leer el contenido del archivo de entrada y escribir
    el resultado en el archivo de salida. Por ahora, simplemente copia el contenido.
    """
    #escribiendo encabezado en el archivo de salida
    outfile.write("mensaje,numero,my_sto,sto,cfo,snr,crc_error,previous_overflow_sum\n")

    # Función para escribir en el archivo de salida
    def write_row(row: Row):
        # Convertir el dataclass a una cadena CSV
        outfile.write(f'"{row.mensaje}",{row.numero},{row.my_sto},{row.sto},{row.cfo},{row.snr},{int(row.crc_error)},{row.overflow_count}\n')

        row.mensaje = ""
        row.numero = -1
        row.my_sto = ""
        row.sto = ""
        row.cfo = ""
        row.snr = ""
        row.crc_error = False
        row.overflow_count = 0

    # Aquí se implementará el pre-procesado deseado.
    row = Row(mensaje="", numero=0, my_sto="", sto="", cfo="", snr="", crc_error=False, overflow_count=0)

    for line in infile:
        line = line.strip()
        # Buscar coincidencias en la línea actual
        if match := OVERFLOW.search(line):
            row.overflow_count += int(match.group(1))
        
        elif match := MESSAGE.search(line):
            row.mensaje = match.group(1) if match.group(1) else line
            row.numero = int(match.group(2)) if match.group(2) else -1

        elif match := MY_STO.search(line):
            row.my_sto = match.group(1)

        elif match := DEF_LOG.search(line):
            row.cfo = match.group(1)
            row.sto = match.group(2)
            row.snr = match.group(3)
        
        elif match := CRC.search(line): # final
            row.crc_error = match.group(1) == "invalid"
            # Escribir la fila en el archivo de salida
            write_row(row)
        else:
            # Si no hay coincidencias, se puede decidir qué hacer (opcional)
            pass

def process_files(input_folder, output_folder, slow_down: float):
    # Asegurarse de que la carpeta de salida exista
    os.makedirs(output_folder, exist_ok=True)
    
    # Listar los archivos que cumplen con la regex en la carpeta de entrada
    files = [f for f in os.listdir(input_folder) if FILE_REGEX.match(f)]
    
    # Barra de carga para el procesamiento de archivos
    for filename in tqdm(files, desc="Procesando archivos"):
        match = FILE_REGEX.match(filename)
        if match:
            freq, distance, version = match.groups()
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename.replace('.txt', '.csv'))
            
            with open(input_file_path, 'r', encoding='utf-8', errors='replace') as infile, \
                 open(output_file_path, 'w', encoding='utf-8') as outfile:
                pre_process(infile, outfile, freq, distance, version)
                
            # Opcional: mensaje de confirmación por archivo
            # print(f"Procesado: {filename}")
            sleep(slow_down)  # Simulación de tiempo de procesamiento

def main():
    parser = argparse.ArgumentParser(description="Script para procesar archivos según una regex")
    parser.add_argument("--input_folder", default="base_txt",
                        help="Carpeta de entrada con los archivos (por defecto: base_txt)")
    parser.add_argument("--output_folder", default="preprocessed_csv",
                        help="Carpeta de salida donde se guardarán los resultados (por defecto: preprocessed_csv)")
    parser.add_argument("--slow-down", type=float, default=0.3,
                        help="Tiempo de retardo en segundos durante el procesamiento de cada archivo (por defecto: 0.3)")
    args = parser.parse_args()
    
    process_files(args.input_folder, args.output_folder, args.slow_down)

if __name__ == "__main__":
    main()
