# Proyek Monitoring Mesin DF (Modbus ke Web)
    ```bash
raspi/
├── modbus_reader.py
├── modbusRtu_reader.py
├── .env
└── requirements.txt
    ```

### Setup Raspberry Pi

1.  **Navigasi ke direktori raspi:**
    ```bash
    cd raspi
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Konfigurasi `.env`**:
    Buat file baru bernama `.env` di dalam direktori `raspi/`. Salin konten di bawah ini dan sesuaikan dengan koneksi mesin Anda.

    **Untuk Modbus TCP/IP:**
    ```ini
    # raspi/.env (Contoh untuk TCP/IP)
    API_URL=

    # Kosongkan parameter RTU
    SERIAL_PORT=
    BAUDRATE=

    # Isi parameter TCP/IP
    MODBUS_IP=192.168.x.x
    MODBUS_PORT=502

    # Register (sesuaikan dengan perangkat Anda)
    #Tutorial mapping address: http://193.36.146.242/V6-Modbus_Slave.PDF
    REGISTER_TEMP=
    REGISTER_BTN=
    BIT_POS_BTN=
    ```

    **Untuk Modbus RTU:**
    ```ini
    # raspi/.env (Contoh untuk RTU)
    API_URL=

    # Isi parameter RTU
    SERIAL_PORT=/dev/xxxx
    BAUDRATE=9600
    PARITY=N
    STOPBITS=1
    BYTESIZE=8

    # Kosongkan parameter TCP/IP
    MODBUS_IP=
    MODBUS_PORT=

    # Register (sesuaikan dengan perangkat Anda)
    REGISTER_TEMP=
    REGISTER_BTN=
    BIT_POS_BTN=
    ```

Berikut adalah versi README yang siap Anda gunakan untuk proyek GitHub Anda:

---

# 📡 Modbus Master (Raspberry Pi)

Bagian ini bertanggung jawab untuk berkomunikasi langsung dengan perangkat industri (PLC/HMI) melalui protokol **Modbus**. Terdapat dua skrip utama yang disediakan untuk mengakomodasi metode koneksi yang berbeda: `modbus_reader.py` (untuk Modbus TCP/IP) dan `modbusRtu_reader.py` (untuk Modbus RTU).

##  Arsitektur Skrip

Kedua skrip dirancang menggunakan arsitektur **multi-threading Producer-Consumer** untuk memastikan keandalan dan efisiensi:

* **Thread Pembaca (Producer)**: Membaca data dari perangkat Modbus secara periodik. Proses ini terus berjalan meskipun koneksi ke backend API sedang lambat atau terputus.
* **Thread Pengirim (Consumer)**: Mengirimkan data terbaru ke backend API.

Desain ini memastikan bahwa data **real-time tetap diprioritaskan**, dan sistem tetap responsif terhadap kondisi mesin.

## 📁 Skrip yang Tersedia

### 1. `modbus_reader.py` (untuk Modbus TCP/IP)

* **Koneksi**: Melalui jaringan Ethernet (LAN/WiFi) menggunakan alamat IP dan port.
* **Penggunaan**: Cocok untuk perangkat modern yang terhubung ke jaringan lokal.

### 2. `modbusRtu_reader.py` (untuk Modbus RTU)

* **Koneksi**: Melalui koneksi serial, seperti USB to RS485/RS232.
* **Penggunaan**: Cocok untuk perangkat lama atau yang hanya mendukung koneksi serial langsung.

## ⚠️ Fitur Penanganan Error

Jika koneksi ke perangkat Modbus gagal, skrip akan otomatis mengirimkan payload dengan status `error_modbus_connection` ke backend. Hal ini memungkinkan frontend untuk menampilkan status koneksi yang akurat.

## ⚙️ Konfigurasi & Menjalankan Skrip

Semua parameter seperti alamat IP, port, alamat register, dan URL API diatur melalui file `.env` di dalam folder `raspi/`. Contoh file `.env` sudah disediakan, Anda hanya perlu menyesuaikannya.

### Menjalankan Skrip:

```bash
# Untuk koneksi Modbus TCP/IP:
python modbus_reader.py

# Untuk koneksi Modbus RTU:
python modbusRtu_reader.py
```

## 🔍 Perbedaan Utama

| Fitur              | `modbus_reader.py` (TCP/IP)       | `modbusRtu_reader.py` (RTU)      |
| ------------------ | --------------------------------- | --------------------------------- |
| **Koneksi Fisik**  | Jaringan Ethernet (LAN/WiFi)      | Koneksi Serial (RS485/RS232)      |
| **Library Client** | `ModbusTcpClient`                 | `ModbusSerialClient`              |
| **Parameter .env** | `MODBUS_IP`, `MODBUS_PORT`        | `SERIAL_PORT`, `BAUDRATE`, dll.   |
| **Logika Kerja**   | Identik (Multi-thread, Real-time) | Identik (Multi-thread, Real-time) |


---

