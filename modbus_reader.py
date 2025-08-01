import os
import time
import requests
import threading
from pymodbus.client import ModbusTcpClient
from dotenv import load_dotenv


load_dotenv()

# Konfigurasi dari .env 
MODBUS_IP = os.getenv('MODBUS_IP')
MODBUS_PORT = int(os.getenv('MODBUS_PORT', 502))
API_URL = os.getenv('API_URL')
NO_MC = int(os.getenv('NO_MC'))
REGISTER_TEMP = int(os.getenv('REGISTER_TEMP'))
REGISTER_SEAM = int(os.getenv('REGISTER_seam'))
# REGISTER_SEAM_RIGHT = int(os.getenv('REGISTER_SEAM_RIGHT'))
REGISTER_LEVEL = int(os.getenv('REGISTER_LEVEL'))
REGISTER_PROCESS = int(os.getenv('REGISTER_PROCESS'))
REGISTER_PTRN = int(os.getenv('REGISTER_PTRN'))
REGISTER_STEP = int(os.getenv('REGISTER_STEP'))
REGISTER_ON_MC = int(os.getenv('REGISTER_ON_MC'))

READ_INTERVAL_SECONDS = 2

latest_data = None
# Lock ini memastikan hanya satu thread yang bisa mengakses latest_data pada satu waktu.
data_lock = threading.Lock()

#  Fungsi untuk Thread Pembaca Modbus 
def modbus_reader_thread():
   
    print("[Reader] Thread pembaca Modbus dimulai.")
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    
    while True:
        global latest_data
        try:
            client.connect()
            
            temp_response = client.read_holding_registers(REGISTER_TEMP, count=1, slave=1)
            seam_response = client.read_holding_registers(REGISTER_SEAM, count=1, slave=1)
            # seamR_response = client.read_holding_registers(REGISTER_SEAM_RIGHT, count=1, slave=1)
            level_response = client.read_holding_registers(REGISTER_LEVEL, count=1, slave=1)
            process_response = client.read_holding_registers(REGISTER_PROCESS, count=1, slave=1)
            ptrn_response = client.read_holding_registers(REGISTER_PTRN, count=1, slave=1)
            step_response = client.read_holding_registers(REGISTER_STEP, count=1, slave=1)
            machine_on_response = client.read_holding_registers(REGISTER_ON_MC, count=10, slave=1)
            
            if temp_response.isError() :
                print(f"[Reader] Error membaca register suhu : {temp_response}")
                continue # Coba lagi di iterasi berikutnya
            temperature = temp_response.registers[0] / 10.0
            
            if seam_response.isError() :
                print(f"[Reader] Error membaca register seam kiri: {seam_response}")
                continue # Coba lagi di iterasi berikutnya
            seam = seam_response.registers[0] 

            # if seamR_response.isError() :
            #     print(f"[Reader] Error membaca register seam kanan: {seamR_response}")
            #     continue # Coba lagi di iterasi berikutnya
            # seam_right = seamR_response.registers[0] 

            if level_response.isError() :
                print(f"[Reader] Error membaca register level: {level_response}")
                continue # Coba lagi di iterasi berikutnya
            level = level_response.registers[0] 

            if process_response.isError():
                print(f"[Reader] Error membaca register tombol: {process_response}")
                continue
            process = process_response.registers[0]

            if ptrn_response.isError():
                print(f"[Reader] Error membaca register tombol: {ptrn_response}")
                continue
            ptrn = ptrn_response.registers[0]

            if step_response.isError():
                print(f"[Reader] Error membaca register tombol: {step_response}")
                continue
            step = step_response.registers[0]

            if machine_on_response.isError():
                print(f"[Reader] Error membaca register tombol: {machine_on_response}")
                continue
            machine_on = machine_on_response.registers[9]



            # Send data yang berhasil dibaca 
            data_read = {"mc":NO_MC,
                         "temperature": temperature, 
                         "seam": seam, 
                        #  "seam_right": seam_right, 
                         "level": level,
                         "process": process,
                         "ptrn": ptrn,
                         "step": step,
                         "machine_on": machine_on,                
                        "status": True}
            with data_lock:
                latest_data = data_read
            print(f"[Reader] Data dibaca : {data_read}")

        except Exception as e:
            print(f"[Reader] Koneksi atau pembacaan Modbus gagal: {e}")
            error_payload = {"mc":NO_MC,
                         "temperature": 0.0, 
                         "seam": 0, 
                        #  "seam_right": seam_right, 
                         "level": 0,
                         "process": 0,
                         "ptrn": 0,
                         "step": 0,
                         "machine_on": 0,                
                        "status": False
            }
            with data_lock:
                latest_data = error_payload
            
            print(f"[Reader] Status error dikirim: {error_payload}")
        finally:
            if client.is_socket_open():
                client.close()
            # Tunggu baca
            time.sleep(READ_INTERVAL_SECONDS)

#  Fungsi untuk Thread Pengirim API 
def api_sender_thread():
   
    print("[Sender] Thread pengirim API dimulai.")
    while True:
        global latest_data
        data_to_send = None

        # Mengunci akses sebelum membaca dan menghapus 
        with data_lock:
            if latest_data is not None:
                data_to_send = latest_data
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
              
                print(f"[Sender] Tidak dapat terhubung ke API: {e}")
        
        time.sleep(0.1)


if __name__ == "__main__":
    print(" Modbus Reader  Dimulai ")
    print(f"Target IP: {MODBUS_IP}:{MODBUS_PORT}")
    print(f"API Endpoint: {API_URL}")
 
   
    reader = threading.Thread(target=modbus_reader_thread, daemon=True)
    reader.start()

    sender = threading.Thread(target=api_sender_thread, daemon=True)
    sender.start()

    # keep program utama tetaprunning
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")

