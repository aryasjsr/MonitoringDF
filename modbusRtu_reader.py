# raspi/modbus_reader_rtu.py

import os
import time
import requests
import threading
import queue

from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

# --- Konfigurasi dari .env untuk Modbus RTU ---
# Parameter koneksi serial
SERIAL_PORT = os.getenv('SERIAL_PORT') 
BAUDRATE = int(os.getenv('BAUDRATE', 9600))
PARITY = os.getenv('PARITY', 'N') 
STOPBITS = int(os.getenv('STOPBITS', 1))
BYTESIZE = int(os.getenv('BYTESIZE', 8))

API_URL = os.getenv('API_URL')
REGISTER_TEMP = int(os.getenv('REGISTER_TEMP'))
REGISTER_BTN = int(os.getenv('REGISTER_BTN'))
BIT_POS_BTN = int(os.getenv('BIT_POS_BTN'))
READ_INTERVAL_SECONDS = 2

# Antrian (Queue) untuk komunikasi antar thread
data_queue = queue.Queue()

# --- Fungsi untuk Thread Pembaca Modbus RTU (Producer) ---
def modbus_reader_thread():

    print("[Reader RTU] Thread pembaca Modbus RTU dimulai.")
    
    # Inisialisasi client untuk Modbus RTU
    client = ModbusSerialClient(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        timeout=1
    )
    
    while True:
        try:
            if not client.is_socket_open():
                client.connect()
            
       
            temp_response = client.read_holding_registers(REGISTER_TEMP, count=1, slave=1)
            if temp_response.isError():
                print(f"[Reader RTU] Error membaca register suhu: {temp_response}")
                continue
            
            temperature = temp_response.registers[0] / 10.0
            
            btn_response = client.read_holding_registers(REGISTER_BTN, count = 1, slave=1)
            if btn_response.isError():
                print(f"[Reader RTU] Error membaca register tombol: {btn_response}")
                continue

            register_value = btn_response.registers[0]
            button_status = bool((register_value >> BIT_POS_BTN) & 1)

            # Masukkan data ke antrian
            data_to_send = {"temperature": temperature, "button_on": button_status}
            data_queue.put(data_to_send)
            print(f"[Reader RTU] Data dibaca dan dimasukkan ke antrian: {data_to_send}")

        except Exception as e:
            print(f"[Reader RTU] Koneksi atau pembacaan Modbus RTU gagal: {e}")
        finally:
            # Tidak perlu close() di setiap loop untuk serial, cukup jaga koneksi
            time.sleep(READ_INTERVAL_SECONDS)
    
    # Tutup koneksi saat thread selesai (meskipun dalam kasus ini tidak akan pernah tercapai)
    client.close()

# --- Fungsi untuk Thread Pengirim API (Consumer) ---
# FUNGSI INI TIDAK PERLU DIUBAH SAMA SEKALI
def api_sender_thread():
    """
    Thread ini mengambil data dari data_queue dan mengirimkannya ke API.
    """
    print("[Sender] Thread pengirim API dimulai.")
    while True:
        try:
            payload = data_queue.get()
            
            print(f"[Sender] Mengambil data dari antrian, mengirim ke API: {payload}")
            response = requests.post(API_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"[Sender] Sukses kirim data. Status: {response.status_code}")
            else:
                print(f"[Sender] Gagal kirim data. Status: {response.status_code}, Response: {response.text}")

            data_queue.task_done()

        except requests.exceptions.RequestException as e:
            print(f"[Sender] Tidak dapat terhubung ke API: {e}")
        except Exception as e:
            print(f"[Sender] Terjadi error tak terduga: {e}")


if __name__ == "__main__":
    print("--- Modbus RTU Reader Multi-Threaded Dimulai ---")
    print(f"Serial Port: {SERIAL_PORT}, Baudrate: {BAUDRATE}")
    print(f"API Endpoint: {API_URL}")

    if not SERIAL_PORT:
        print("ERROR: SERIAL_PORT tidak diatur di file .env. Program berhenti.")
        exit()

    # Membuat dan memulai thread pembaca
    reader = threading.Thread(target=modbus_reader_thread, daemon=True)
    reader.start()

    # Membuat dan memulai thread pengirim
    sender = threading.Thread(target=api_sender_thread, daemon=True)
    sender.start()

    # Jaga agar program utama tetap berjalan
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
