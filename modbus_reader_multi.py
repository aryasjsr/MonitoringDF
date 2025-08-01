# raspi/multi_machine_reader.py

import os
import time
import requests
import threading
import json
from pymodbus.client import ModbusTcpClient
from dotenv import load_dotenv

load_dotenv()

# --- Konfigurasi Global ---
API_URL = os.getenv('API_URL')
CONFIG_FILE = 'machines.json'
READ_INTERVAL_SECONDS = 2

# --- Pengganti Queue: Variabel Bersama & Kunci ---
# Dictionary ini akan menyimpan data terbaru untuk SETIAP mesin.
# Key: noMc, Value: payload data
latest_data_per_machine = {}
# Lock untuk melindungi akses ke dictionary di atas.
data_lock = threading.Lock()

# --- Fungsi Generik untuk Membaca Data dari Satu Mesin (Producer) ---
def machine_reader_thread(machine_config: dict):
    """
    Satu thread dari fungsi ini berjalan untuk setiap mesin.
    Ia membaca data dan MENIMPA data terbaru di 'latest_data_per_machine'.
    """
    global latest_data_per_machine
    no_mc = machine_config['noMc']
    ip = machine_config['ip_address']
    port = machine_config['port']
    regs = machine_config['registers']
    
    print(f"[Reader MC-{no_mc}] Thread untuk mesin di {ip} dimulai.")
    client = ModbusTcpClient(ip, port=port)

    while True:
        try:
            client.connect()
            
            temp_val = client.read_holding_registers(regs['temperature'], count=1, slave=1).registers[0] / 10.0
            seam_val = client.read_holding_registers(regs['seam'], count=1, slave=1).registers[0]
            level_val = client.read_holding_registers(regs['level'], count=1, slave=1).registers[0]
            process_val = client.read_holding_registers(regs['process'], count=1, slave=1).registers[0]
            ptrn_val = client.read_holding_registers(regs['pattern'], count=1, slave=1).registers[0]
            step_val = client.read_holding_registers(regs['step'], count=1, slave=1).registers[0]
            machine_on_val = client.read_holding_registers(regs['machine_on'], count=10, slave=1).registers[7]

            data_read = {
                "noMc": no_mc, "temp": temp_val, "seam": seam_val, "level": level_val,
                "process": process_val, "patern": ptrn_val, "step": step_val,
                "machine_on": machine_on_val, "status": True
            }
            
            # Kunci akses dan timpa data terbaru untuk mesin ini
            with data_lock:
                latest_data_per_machine[no_mc] = data_read
            
            print(f"[Reader MC-{no_mc}] Data diperbarui: {data_read}")

        except Exception as e:
            print(f"[Reader MC-{no_mc}] Gagal membaca dari {ip}: {e}")
            error_payload = {
                "noMc": no_mc, "temp": 0, "seam": 0, "level": 0, "process": 0,
                "patern": 0, "step": 0, "machine_on": 0, "status": False
            }
            with data_lock:
                latest_data_per_machine[no_mc] = error_payload
        finally:
            if client.is_socket_open():
                client.close()
            time.sleep(READ_INTERVAL_SECONDS)

# --- Thread Pengirim API (Consumer) ---
def api_sender_thread():
    """
    Satu thread ini secara periodik memeriksa apakah ada data baru,
    mengirimkannya, lalu menghapusnya agar tidak dikirim ganda.
    """
    global latest_data_per_machine
    print("[Sender] Thread pengirim API dimulai.")
    while True:
        data_to_send_batch = {}
        
        # Kunci akses untuk menyalin dan menghapus data dengan aman
        with data_lock:
            if latest_data_per_machine:
                # Salin semua data terbaru yang ada
                data_to_send_batch = latest_data_per_machine.copy()
                # Kosongkan data bersama agar tidak dikirim lagi
                latest_data_per_machine.clear()
        
        # Jika ada data yang perlu dikirim
        if data_to_send_batch:
            for no_mc, payload in data_to_send_batch.items():
                try:
                    print(f"[Sender] Mengirim data untuk MC-{no_mc}: {payload}")
                    response =requests.post(API_URL, json=payload, timeout=10)
                    if response.status_code == 200:
                        print(f"[Sender] Sukses kirim data.")
                    else:
                        print(f"[Sender] Gagal kirim data. Status: {response.status_code}")
                except Exception as e:
                    # Jika pengiriman gagal, data akan hilang (sesuai permintaan)
                    print(f"[Sender] Gagal mengirim data untuk MC-{no_mc}: {e}")
        
        # Beri jeda singkat agar loop tidak membebani CPU
        time.sleep(0.2)

if __name__ == "__main__":
    print("--- Multi-Machine Modbus Reader (Real-time Overwrite) Dimulai ---")
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            all_machines = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File konfigurasi '{CONFIG_FILE}' tidak ditemukan!")
        exit()

    # Membuat dan memulai thread pengirim
    sender = threading.Thread(target=api_sender_thread, daemon=True)
    sender.start()

    # Membuat dan memulai satu thread pembaca untuk setiap mesin
    for machine in all_machines:
        reader = threading.Thread(target=machine_reader_thread, args=(machine,), daemon=True)
        reader.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
