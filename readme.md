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

 Komponen Pengumpul Data (Raspberry Pi)
Bagian ini bertanggung jawab untuk berkomunikasi langsung dengan perangkat industri (PLC/HMI) melalui protokol Modbus. Terdapat dua skrip yang disediakan untuk mengakomodasi metode koneksi yang berbeda.

Arsitektur Skrip
Kedua skrip dirancang menggunakan arsitektur multi-threading (Producer-Consumer) untuk memastikan keandalan dan efisiensi:

Thread Pembaca (Producer): Fokus utamanya adalah membaca data dari perangkat Modbus secara periodik. Proses ini tidak akan terganggu meskipun koneksi ke backend API lambat atau terputus.

Thread Pengirim (Consumer): Fokus utamanya adalah mengirimkan data terbaru yang telah dibaca ke backend API.

Desain ini memastikan data real-time selalu diprioritaskan dan sistem tetap responsif terhadap kondisi mesin.

Skrip yang Tersedia
1. modbus_reader.py (untuk Modbus TCP/IP)
Koneksi: Menggunakan jaringan Ethernet (LAN/WiFi) untuk terhubung ke perangkat melalui alamat IP dan Port.

Penggunaan: Cocok untuk perangkat modern yang terhubung ke jaringan lokal.

2. modbus_reader_rtu.py (untuk Modbus RTU)
Koneksi: Menggunakan koneksi serial (misalnya, melalui converter USB to RS485/RS232).

Penggunaan: Cocok untuk perangkat yang memerlukan koneksi serial langsung.

Fitur Penanganan Error
Jika koneksi ke perangkat Modbus terputus, kedua skrip akan secara otomatis mengirimkan payload dengan status error_modbus_connection ke backend. Hal ini memungkinkan dasbor frontend untuk menampilkan status koneksi yang akurat kepada pengguna.

Konfigurasi dan Menjalankan
Semua parameter (alamat IP, port, parameter serial, alamat register, dan URL API) diatur di dalam file raspi/.env. Pastikan Anda mengisi file ini sesuai dengan metode koneksi yang Anda gunakan sebelum menjalankan skrip.

Menjalankan Skrip:

# Pilih skrip yang sesuai dengan koneksi Anda
# Untuk TCP/IP:
python modbus_reader.py

# Untuk RTU:
python modbus_reader_rtu.py

Perbedaan Utama
Fitur

modbus_reader.py (TCP/IP)

modbus_reader_rtu.py (RTU)

Koneksi Fisik

Jaringan Ethernet (LAN/WiFi)

Koneksi Serial (RS485/RS232)

Library Client

ModbusTcpClient

ModbusSerialClient

Parameter .env

MODBUS_IP, MODBUS_PORT

SERIAL_PORT, BAUDRATE, PARITY, dll.

Logika Kerja

Identik (Multi-thread, Real-time)

Identik (Multi-thread, Real-time)


---

