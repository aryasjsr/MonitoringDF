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
REGISTER_SEAM_LEFT = int(os.getenv('REGISTER_SEAM_LEFT'))
REGISTER_SEAM_RIGHT = int(os.getenv('REGISTER_SEAM_RIGHT'))
REGISTER_LEVEL = int(os.getenv('REGISTER_LEVEL'))
REGISTER_SET_TEMP = int(os.getenv('REGISTER_SET_TEMP'))
REGISTER_BTN = int(os.getenv('REGISTER_BTN'))
BIT_POS_BTN = int(os.getenv('BIT_POS_BTN'))
READ_INTERVAL_SECONDS = 2 # Interval pembacaan data

latest_data = None
# Lock ini memastikan hanya satu thread yang bisa mengakses latest_data pada satu waktu.
data_lock = threading.Lock()

#  Fungsi untuk Thread Pembaca Modbus (Producer) 
def modbus_reader_thread():
   
    print("[Reader] Thread pembaca Modbus dimulai.")
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    
    while True:
        global latest_data
        try:
            client.connect()
            
            temp_response = client.read_holding_registers(REGISTER_TEMP, count=1, slave=1)
            seamL_response = client.read_holding_registers(REGISTER_SEAM_LEFT, count=1, slave=1)
            seamR_response = client.read_holding_registers(REGISTER_SEAM_RIGHT, count=1, slave=1)
            level_response = client.read_holding_registers(REGISTER_LEVEL, count=1, slave=1)
            setTemp_response = client.read_holding_registers(REGISTER_SET_TEMP, count=1, slave=1)
            
            if temp_response.isError() :
                print(f"[Reader] Error membaca register suhu : {temp_response}")
                continue # Coba lagi di iterasi berikutnya
            
            temperature = temp_response.registers[0] / 10.0
            
            if seamL_response.isError() :
                print(f"[Reader] Error membaca register seam kiri: {seamL_response}")
                continue # Coba lagi di iterasi berikutnya
            seam_left = seamL_response.registers[0] 

            if seamR_response.isError() :
                print(f"[Reader] Error membaca register seam kanan: {seamR_response}")
                continue # Coba lagi di iterasi berikutnya
            seam_right = seamR_response.registers[0] 

            if level_response.isError() :
                print(f"[Reader] Error membaca register level: {level_response}")
                continue # Coba lagi di iterasi berikutnya
            level = level_response.registers[0] 

            if setTemp_response.isError() :
                print(f"[Reader] Error membaca register set temperature: {setTemp_response}")
                continue # Coba lagi di iterasi berikutnya
            set_temp = setTemp_response.registers[0] / 10.0

            btn_response = client.read_holding_registers(REGISTER_BTN, count=1, slave=1)
            if btn_response.isError():
                print(f"[Reader] Error membaca register tombol: {btn_response}")
                continue

            register_value = btn_response.registers[0]
            button_status = bool((register_value >> BIT_POS_BTN) & 1)

            # Send data yang berhasil dibaca 
            data_read = {"temperature": temperature, "seam_left": seam_left, "seam_right": seam_right, "level": level,"set_temp": set_temp, "button_on": button_status,"status": "ok"}
            with data_lock:
                latest_data = data_read
            print(f"[Reader] Data dibaca : {data_read}")

        except Exception as e:
            print(f"[Reader] Koneksi atau pembacaan Modbus gagal: {e}")
            error_payload = {
                "temperature": 0, # Nilai default
                "button_on": False, # Nilai default yang aman
                "status": "error_modbus_connection" # Status error yang jelas
            }
            with data_lock:
                latest_data = error_payload
            
            print(f"[Reader] Status error dikirim: {error_payload}")
        finally:
            if client.is_socket_open():
                client.close()
            # Tunggu baca
            time.sleep(READ_INTERVAL_SECONDS)

#  Fungsi untuk Thread Pengirim API (Consumer) 
def api_sender_thread():
   
    print("[Sender] Thread pengirim API dimulai.")
    while True:
        global latest_data
        data_to_send = None

        # Mengunci akses sebelum membaca dan menghapus dari variabel bersama
        with data_lock:
            if latest_data is not None:
                # Salin data ke variabel lokal
                data_to_send = latest_data
                # Hapus data dari variabel bersama agar tidak dikirim lagi
                latest_data = None
        
        # Jika ada data baru untuk dikirim
        if data_to_send:
            try:
                print(f"[Sender] Mengirim data baru ke API: {data_to_send}")
                response = requests.post(API_URL, json=data_to_send, timeout=10)
                if response.status_code == 200:
                    print(f"[Sender] Sukses kirim data.")
                else:
                    print(f"[Sender] Gagal kirim data. Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                # Jika pengiriman gagal, data akan hilang. Ini sesuai permintaan.
                print(f"[Sender] Tidak dapat terhubung ke API: {e}")
        
        # Beri jeda singkat agar loop tidak membebani CPU
        time.sleep(0.1)


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
        print("\nProgram dihentikan.")

