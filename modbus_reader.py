# raspi/modbus_reader.py

import os
import time
import requests
import threading
import queue
from pymodbus.client import ModbusTcpClient
from dotenv import load_dotenv


load_dotenv()

# Konfigurasi dari .env 
MODBUS_IP = os.getenv('MODBUS_IP')
MODBUS_PORT = int(os.getenv('MODBUS_PORT', 502))
API_URL = os.getenv('API_URL')
REGISTER_TEMP = int(os.getenv('REGISTER_TEMP'))
REGISTER_BTN = int(os.getenv('REGISTER_BTN'))
BIT_POS_BTN = int(os.getenv('BIT_POS_BTN'))
READ_INTERVAL_SECONDS = 2 # Interval pembacaan data

#  Antrian (Queue) untuk Komunikasi antar Thread 
# Queue ini aman digunakan oleh banyak thread (thread-safe)
data_queue = queue.Queue()

#  Fungsi untuk Thread Pembaca Modbus (Producer) 
def modbus_reader_thread():
    """
    Thread ini bertugas membaca data dari Modbus secara periodik
    dan menaruh hasilnya ke dalam data_queue.
    """
    print("[Reader] Thread pembaca Modbus dimulai.")
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    
    while True:
        try:
            client.connect()
            
            # Baca register suhu
            temp_response = client.read_holding_registers(REGISTER_TEMP, count=1, slave=1)
            if temp_response.isError():
                print(f"[Reader] Error membaca register suhu: {temp_response}")
                continue # Coba lagi di iterasi berikutnya
            
            temperature = temp_response.registers[0] / 10.0
            
            # Baca register tombol
            btn_response = client.read_holding_registers(REGISTER_BTN, count=1, slave=1)
            if btn_response.isError():
                print(f"[Reader] Error membaca register tombol: {btn_response}")
                continue

            register_value = btn_response.registers[0]
            button_status = bool((register_value >> BIT_POS_BTN) & 1)

            # Send data yang berhasil dibaca ke dalam antrian
            data_to_send = {"temperature": temperature, "button_on": button_status}
            data_queue.put(data_to_send)
            print(f"[Reader] Data dibaca dan dimasukkan ke antrian: {data_to_send}")

        except Exception as e:
            print(f"[Reader] Koneksi atau pembacaan Modbus gagal: {e}")
        finally:
            if client.is_socket_open():
                client.close()
            # Tunggu sebelum membaca lagi
            time.sleep(READ_INTERVAL_SECONDS)

#  Fungsi untuk Thread Pengirim API (Consumer) 
def api_sender_thread():
    """
    Thread ini bertugas mengambil data dari data_queue (jika ada)
    dan mengirimkannya ke API.
    """
    print("[Sender] Thread pengirim API dimulai.")
    while True:
        try:
            # Ambil data dari antrian. .get() akan menunggu (block) sampai ada item.
            payload = data_queue.get()
            
            print(f"[Sender] Mengambil data dari antrian, mengirim ke API: {payload}")
            response = requests.post(API_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"[Sender] Sukses kirim data. Status: {response.status_code}")
            else:
                print(f"[Sender] Gagal kirim data. Status: {response.status_code}, Response: {response.text}")

            # Memberi tahu antrian bahwa tugas untuk item ini sudah selesai
            data_queue.task_done()

        except requests.exceptions.RequestException as e:
            print(f"[Sender] Tidak dapat terhubung ke API: {e}")
        except Exception as e:
            print(f"[Sender] Terjadi error tak terduga: {e}")


if __name__ == "__main__":
    print(" Modbus Reader Multi-Threaded Dimulai ")
    print(f"Target IP: {MODBUS_IP}:{MODBUS_PORT}")
    print(f"API Endpoint: {API_URL}")
 
    # Membuat dan memulai thread pembaca sebagai daemon thread
    # Daemon thread akan otomatis berhenti jika program utama berhenti
    reader = threading.Thread(target=modbus_reader_thread, daemon=True)
    reader.start()

    # Membuat dan memulai thread pengirim sebagai daemon thread
    sender = threading.Thread(target=api_sender_thread, daemon=True)
    sender.start()

    # keep program utama tetaprunning
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")

