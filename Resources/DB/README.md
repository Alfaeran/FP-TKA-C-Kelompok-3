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
* [cite_start]**Method & Endpoint:** `POST /order` [cite: 11]
* [cite_start]**Deskripsi:** Membuat pesanan baru dan menyimpan data dengan status awal "pending"[cite: 11, 12].
* [cite_start]**Status Code:** 201 Created [cite: 13]
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![POST Create Order](./assets/Screenshot%20(2172).png)

</details>

### 2. Get Order Status
* [cite_start]**Method & Endpoint:** `GET /order/<order_id>` [cite: 14]
* [cite_start]**Deskripsi:** Mengambil status dan detail sebuah pesanan berdasarkan `order_id`[cite: 14].
* [cite_start]**Status Code:** 200 OK (Berhasil) & 404 Not Found (Skenario Error Handling) [cite: 15]
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman (200 OK)</summary>

![GET Order Status OK](./assets/Screenshot%20(2173).png)

</details>
<details>
<summary>Klik untuk melihat Screenshot Postman (404 Not Found)</summary>

![GET Order Status 404](./result/get_order_404.png)

</details>

### 3. Update Order Status
* [cite_start]**Method & Endpoint:** `PUT /order/<order_id>` [cite: 17]
* [cite_start]**Deskripsi:** Mengubah status pesanan dari "pending" menjadi "completed"[cite: 17].
* [cite_start]**Status Code:** 200 OK [cite: 18]
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![PUT Update Order](./result/put_order.png)

</details>

### 4. Get Order History
* [cite_start]**Method & Endpoint:** `GET /orders` [cite: 15]
* [cite_start]**Deskripsi:** Mengambil seluruh riwayat pesanan yang diurutkan dari paling baru[cite: 15].
* [cite_start]**Status Code:** 200 OK [cite: 16]
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Postman</summary>

![GET Order History](./result/get_orders.png)

</details>

### 5. Tampilan Frontend
* [cite_start]**Deskripsi:** Antarmuka web yang sudah terhubung dengan backend[cite: 18].
* **Bukti Pengujian:**
<details>
<summary>Klik untuk melihat Screenshot Frontend</summary>

![Tampilan Frontend](./result/frontend.png)

</details>
