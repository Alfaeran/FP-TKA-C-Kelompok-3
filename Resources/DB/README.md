# MongoDB Dump — Order Processing Service

## Isi Dump

| Collection   | Dokumen  | Keterangan                          |
|--------------|----------|-------------------------------------|
| users        | 505      | 5 admin + 500 user biasa            |
| products     | 96       | 7 kategori produk                   |
| orders       | 10.000   | Riwayat transaksi 1 tahun terakhir  |
| audit_logs   | 2.000    | Log aksi admin                      |
| sessions     | 100      | Sample sesi aktif                   |

## Akun Default

| Role  | Email                     | Password     |
|-------|---------------------------|--------------|
| Admin | admin1@tka.its.ac.id      | Admin@12345  |
| Admin | admin2@tka.its.ac.id      | Admin@12345  |
| User  | (lihat collection users)  | User@12345   |

## Cara Restore

```bash
# Restore ke MongoDB lokal
mongorestore --drop dump/

# Restore ke MongoDB remote
mongorestore --uri="mongodb://IP:27017" --drop dump/

# Restore ke MongoDB dengan auth
mongorestore --uri="mongodb://user:pass@IP:27017" --drop dump/
```

## Re-generate Data

Jika ingin generate ulang dengan jumlah berbeda:

```bash
pip install pymongo faker tqdm bcrypt
python generate_dump.py   # output ke folder dump/
```

## Hasil Pengujian Endpoint

Bagian ini mendokumentasikan hasil pengujian fungsionalitas REST API menggunakan Postman. Semua endpoint telah diuji dan berfungsi dengan baik sesuai dengan spesifikasi.

### 1. Create Order
* **Method & Endpoint:** `POST /order`
* **Deskripsi:** Membuat pesanan baru dan menyimpan data dengan status awal "pending".
* **Status Code:** 201 Created
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![POST Create Order](./assets/Screenshot%20(2172).png)

</details>

### 2. Get Order Status
* **Method & Endpoint:** `GET /order/<order_id>`
* **Deskripsi:** Mengambil status dan detail sebuah pesanan berdasarkan `order_id`.
* **Status Code:** 200 OK (Berhasil) & 404 Not Found (Skenario Error Handling)
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman (200 OK)</summary>

![GET Order Status OK](./assets/Screenshot%20(2173).png)

</details>
<details>
<summary>Klik untuk melihat Screenshot Postman (404 Not Found)</summary>

![GET Order Status 404](./assets/Screenshot%20(2174).png)

</details>

### 3. Update Order Status
* **Method & Endpoint:** `PUT /order/<order_id>`
* **Deskripsi:** Mengubah status pesanan dari "pending" menjadi "completed".
* **Status Code:** 200 OK
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![PUT Update Order](./assets/Screenshot%20(2175).png)

</details>

### 4. Get Order History
* **Method & Endpoint:** `GET /orders`
* **Deskripsi:** Mengambil seluruh riwayat pesanan yang diurutkan dari paling baru.
* **Status Code:** 200 OK
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![GET Order History](./assets/Screenshot%20(2176).png)

</details>

### 5. Tampilan Frontend
* **Deskripsi:** Antarmuka web yang sudah terhubung dengan backend.
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Frontend</summary>

![Tampilan Frontend](./assets/Screenshot%20(2177).png)

</details>
