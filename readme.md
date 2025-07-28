# Proyek Monitoring Mesin Industri (Modbus ke Web)

├── raspi/
│   ├── modbus_reader.py      # Skrip untuk Modbus TCP/IP
│   ├── modbus_reader_rtu.py  # Skrip untuk Modbus RTU
│   └── requirements.txt

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

---