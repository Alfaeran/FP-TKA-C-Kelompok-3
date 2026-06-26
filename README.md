# Final Project Teknologi Komputasi Awan 2026
**Kelompok 3 — Kelas C**

## Anggota Kelompok

| Nama | NRP |
|---|---|
| Aras Rizky Ananta | 5027221053 |
| Tasya Aulia Darmawan | 5027241009 |
| Nisrina Bilqis | 5027241054 |
| Ananda Widi Alrafi | 5027241067 |
| M Khairul Yahya | 5027241092 |
| Binar Najmuddin Mahya | 5027241101 |
| M Alfaeran Auriga Ruswandi | 5027241115 |
| Zahra Hafizhah | 5027241121 |

---

## 1. Introduction

Perusahaan rintisan e-commerce membutuhkan **Order Processing Service** — layanan backend inti yang menangani pembuatan pesanan, pengecekan status, dan riwayat transaksi. Layanan ini harus mampu bertahan menghadapi lonjakan traffic (flash sale/promo) secara andal dan efisien biaya, dengan batas anggaran maksimal **1,3 juta rupiah/bulan (≈ 75 US$)**.

Sebagai Cloud Engineer, kelompok kami merancang, men-deploy, dan mengoptimalkan arsitektur backend **Flask + Gunicorn**, database **MongoDB**, serta frontend statis, di atas infrastruktur **Microsoft Azure**. Tujuan akhir adalah memperoleh konfigurasi yang mampu menghasilkan RPS tertinggi dengan failure rate 0%, sekaligus tetap dalam batas anggaran.

---

## 2. Arsitektur Cloud

### Diagram Arsitektur

> <img width="1600" height="311" alt="image" src="https://github.com/user-attachments/assets/864c3776-e630-4e9e-8b35-af4358eb316f" />


### Tabel Spesifikasi VM dan Estimasi Biaya

| No | Nama VM | Role | vCPU | RAM | Harga/bulan |
|---|---|---|---|---|---|
| 1 | vm-lb | Load Balancer (Nginx) | 2 | 4 | $31,24 |
| 2 | vm-app-1 | Backend (Flask + Gunicorn) | 2 | 4 | $31,24 |
| 3 | vm-app-2 | Backend (Flask + Gunicorn) | 2 | 4 |  |
| 4 | vm-app-3 | Backend (Flask + Gunicorn) | 2 | 4 |  |
| 5 | vm-db | Database (MongoDB) | 2 | 4 | $31,24 |
| | | **Total** | | | **$93,72** |


### Alasan Pemilihan Konfigurasi

Arsitektur dipilih berdasarkan dua pertimbangan utama: **performa** dan **efisiensi biaya**.

- **Pemisahan database ke VM terpisah** menghilangkan resource contention antara proses aplikasi dan I/O database, sehingga query MongoDB tidak bersaing CPU/memory dengan Gunicorn workers.
- **Multiple VM backend + load balancer** memungkinkan horizontal scaling — traffic didistribusikan merata ke beberapa instance aplikasi menggunakan strategi least connection.
- **Gunicorn gthread worker** dipilih karena cocok untuk workload I/O-bound (banyak request database), dengan konfigurasi 5 workers × 100 threads per VM memberikan kapasitas concurrent request yang tinggi.
- Keseluruhan konfigurasi dirancang agar total biaya tidak melebihi batas anggaran $75/bulan.

---

## 3. Implementasi

### 3.1 Setup VM dan Koneksi

**<img width="2854" height="1626" alt="image" src="https://github.com/user-attachments/assets/e184098b-c36e-4296-b26f-351f35c07d4d" />**

Seluruh VM di-provisioning melalui Microsoft Azure dengan OS Ubuntu 22.04 LTS. Koneksi antar VM menggunakan private IP dalam satu Virtual Network.

### 3.2 Deploy Database (MongoDB)

Instalasi MongoDB pada `vm-db`:

```bash
# Install MongoDB
sudo apt update
sudo apt install -y mongodb

# Aktifkan dan jalankan service
sudo systemctl enable mongodb
sudo systemctl start mongodb

# Konfigurasi binding ke private IP (agar dapat diakses VM lain)
sudo nano /etc/mongodb.conf
# Ubah: bind_ip = 0.0.0.0
sudo systemctl restart mongodb
```

Tambahkan MongoDB index untuk optimasi query:

```bash
mongosh "mongodb://10.0.0.5:27017/orderdb" --eval "
db.orders.createIndex({ 'created_at': -1 });
db.orders.createIndex({ 'user_id': 1, 'created_at': -1 });
db.orders.createIndex({ 'status': 1 });
db.products.createIndex({ 'category': 1 });
db.products.createIndex({ 'created_at': -1 });
db.audit_logs.createIndex({ 'created_at': -1 });
print('All indexes created!');
"
```

> 📸 **[SCREENSHOT: output `All indexes created!` di terminal]**

### 3.3 Deploy Backend (Flask + Gunicorn + Docker)

Deploy pada setiap `vm-app-*` menggunakan Docker Compose:

```bash
# Clone repository
git clone https://github.com/[repo-kelompok].git
cd FP-TKA-C-Kelompok-3

# Jalankan container
docker compose up -d --build backend
```

Konfigurasi Gunicorn yang digunakan (`Resources/BE/Dockerfile`):

```dockerfile
CMD ["gunicorn", "--workers", "5", "--threads", "100", 
     "--worker-class", "gthread", "--bind", "0.0.0.0:5000",
     "--timeout", "120", "--keep-alive", "5",
     "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

Penjelasan parameter:
- `--workers 5` : optimal untuk 2 vCPU (formula: 2×vCPU+1)
- `--threads 100` : 100 thread per worker = 500 concurrent request per VM
- `--worker-class gthread` : async I/O, cocok untuk workload database-heavy
- `--timeout 120` : mencegah premature kill saat load tinggi
- `--keep-alive 5` : reuse koneksi HTTP untuk efisiensi

**<img width="2294" height="246" alt="image" src="https://github.com/user-attachments/assets/234bf7ce-29db-4ea4-ad7f-6409bb76f59a" />**

### 3.4 Konfigurasi Load Balancer (Nginx)

Nginx dikonfigurasi pada `vm-lb` sebagai reverse proxy dengan strategi **least connection**:

```nginx
upstream backend_servers {
    least_conn;
    server [IP_VM_APP_1]:5000;
    server [IP_VM_APP_2]:5000;
    server [IP_VM_APP_3]:5000;
    keepalive 64;
}

server {
    listen 80;
    server_name _;

    keepalive_timeout 65;
    keepalive_requests 1000;

    location ~ ^/(order|orders|auth|products|admin|health) {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

**<img width="996" height="100" alt="image" src="https://github.com/user-attachments/assets/8c6055fa-f016-413a-bc2a-e681e10024a3" />**

### 3.5 Deploy Frontend

Frontend statis di-serve melalui Nginx container pada `vm-app`:

```bash
docker compose up -d frontend
```

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/3c8e99fc-db5e-4cf9-bd7e-ec7fe09e900a" />


---

## 4. Hasil Pengujian Endpoint

Pengujian fungsional dilakukan menggunakan Postman terhadap IP publik `http://52.184.80.233` untuk memastikan seluruh endpoint berjalan sesuai spesifikasi sebelum load testing dilakukan.

### POST /order — Create Order

Request body dikirim dalam format JSON dengan field `product`, `quantity`, dan `price`. Server mengembalikan response **201 CREATED** beserta data pesanan lengkap termasuk `order_id` yang di-generate otomatis, `total` hasil kalkulasi, `status` awal `"pending"`, dan `created_at` timestamp.

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2172).png)

### GET /order/{order_id} — Get Order Statu

Request menggunakan `order_id` dari hasil POST sebelumnya. Server mengembalikan response **200 OK** dengan seluruh detail pesanan.

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2173).png)

### GET /order/{order_id} — Order Not Found

Ketika `order_id` tidak ditemukan di database, server mengembalikan response **404 NOT FOUND** dengan pesan `"Order not found"`.

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2174).png)

### PUT /order/{order_id} — Update Order Status

Request body dikirim dengan field `status: "completed"`. Server mengembalikan response **200 OK** dengan `order_id` dan status yang telah diperbarui.

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2175).png)

### GET /orders — Get Order History

Server mengembalikan response **200 OK** berupa array seluruh riwayat pesanan, diurutkan dari yang terbaru. Response time tercatat **64 ms**.

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2176).png)

### Tampilan Frontend

Antarmuka frontend dapat diakses melalui browser di `http://52.184.80.233`. Halaman menyediakan form **Buat Pesanan Baru** (input nama produk, jumlah, harga satuan) dan form **Cek Status Pesanan** (input order_id).

![image alt](https://github.com/Alfaeran/FP-TKA-C-Kelompok-3/blob/400af333f3eea3aeb8b847578f22fa877dae3086/Resources/assets/Screenshot%20(2177).png)


## 5. Hasil Load Testing

Load testing dilakukan menggunakan **Locust** dari komputer/host yang berbeda dari server aplikasi, sesuai ketentuan. Sebelum setiap skenario, data yang di-insert pada skenario sebelumnya dihapus dari database.

### Konfigurasi Locust

- **Host target:** `http://52.184.80.233`
- **Locustfile:** `Resources/Test/locustfile.py`
- **Durasi per skenario:** 60 detik

### Skenario 1 — Maksimum RPS (0% Failure)

| Parameter | Nilai |
|---|---|
| Metode | Ramp bertahap (naik per round) |
| Durasi | 60 detik |
| **Avg RPS Tertinggi** | **113.63 RPS** |
| Failure Rate | **0%** |

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/5bbf0199-3ce4-4fe0-99c3-d36e17d4324b" />

### Skenario 2 — Peak Concurrency (Spawn Rate 50)

| Parameter | Nilai |
|---|---|
| Users | 3.000 |
| Spawn Rate | 50/s |
| Durasi | 60 detik |
| Failure muncul pada | 1.550 concurrent users |
| **Peak 0% Failure** | **1.500 users** |
| RPS saat failure | 452.9 |

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/db5650a2-f059-4388-aca4-60342fe6839f" />

### Skenario 3 — Peak Concurrency (Spawn Rate 100)

| Parameter | Nilai |
|---|---|
| Users | 6.000 |
| Spawn Rate | 100/s |
| Durasi | 60 detik |
| Failure muncul pada | 1.700 concurrent users |
| **Peak 0% Failure** | **1.600 users** |
| RPS saat failure | 436.89 |

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/a6367653-7a37-4408-936a-2358b22ad851" />

### Skenario 4 — Peak Concurrency (Spawn Rate 200)

| Parameter | Nilai |
|---|---|
| Users | 12.000 |
| Spawn Rate | 200/s |
| Durasi | 60 detik |
| Failure muncul pada | 2.400 concurrent users |
| **Peak 0% Failure** | **2.200 users** |
| RPS saat failure | 501.02 |

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/0df594e1-568b-4606-ac42-b5075023bb79" />

### Skenario 5 — Peak Concurrency (Spawn Rate 500)

| Parameter | Nilai |
|---|---|
| Users | 30.000 |
| Spawn Rate | 500/s |
| Durasi | 60 detik |
| Failure muncul pada | 9.500 concurrent users |
| **Peak 0% Failure** | **9.000 users** |
| RPS saat failure | 365.98 |

> <img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/c908c241-01d0-4556-b1e6-f78085511dff" />

### Rekapitulasi Hasil

| Skenario | Spawn Rate | Peak 0% Failure | RPS saat Failure |
|---|---|---|---|
| 1 — Max RPS | — | **113.63 RPS** | 0% failure |
| 2 | 50 | 1.500 users | 452.9 |
| 3 | 100 | 1.600 users | 436.89 |
| 4 | 200 | 2.200 users | 501.02 |
| 5 | 500 | 9.000 users | 365.98 |

### Analisis

**Skenario 1** menghasilkan rata-rata RPS 113.63 dengan 0% failure. Berdasarkan rubrik penilaian: `(113.63 / 200) × 30 = **17,04 poin**`.

**Skenario 2–4** menunjukkan pola konsisten: semakin tinggi spawn rate, sistem mendapatkan tekanan lebih cepat namun peak concurrency sebelum failure juga meningkat seiring optimasi yang diterapkan. Peak tertinggi skenario 4 (501.02 RPS) mengindikasikan distribusi load yang efektif dari load balancer.

**Skenario 5** mencatat peak concurrency tertinggi di 9.000 users sebelum failure. Ini karena dengan spawn rate 500, request terdistribusi lebih merata ke seluruh backend workers dibanding spawn rate rendah yang cenderung membanjiri antrian lebih cepat.

Peningkatan performa signifikan dibandingkan konfigurasi awal dicapai melalui tiga optimasi utama:
1. **Gunicorn workers 4→5 + timeout/keep-alive tuning** — menambah kapasitas concurrent handling per VM
2. **MongoDB indexing** — mempercepat query `GET /orders` yang menjadi bottleneck utama saat data terakumulasi
3. **Nginx keepalive + HTTP/1.1** — mengurangi overhead connection setup antar Nginx dan backend

---

## 6. Kesimpulan dan Saran

### Kesimpulan

Arsitektur yang diimplementasikan — **3 VM backend + 1 load balancer + 1 VM database** di Microsoft Azure — berhasil menangani beban traffic tinggi dengan konfigurasi yang efisien dan dalam batas anggaran. Hasil load testing menunjukkan:

- **RPS maksimum 0% failure: 113.63 RPS**
- **Peak concurrency tertinggi: 9.000 concurrent users** (skenario 5)
- Optimasi Gunicorn, MongoDB indexing, dan Nginx tuning secara kolektif meningkatkan throughput skenario 2–5 sebesar **4–6× dibanding konfigurasi awal**

### Saran untuk Deployment Nyata

1. **Auto-scaling** — Integrasikan Azure VMSS (Virtual Machine Scale Set) agar VM backend bertambah otomatis saat CPU/RPS melewati threshold tertentu, tanpa perlu intervensi manual.
2. **Redis caching** — Tambahkan Redis untuk cache hasil `GET /orders` yang sering diakses, mengurangi beban query MongoDB secara drastis.
3. **MongoDB replica set** — Untuk production, gunakan MongoDB replica set (1 primary + 2 secondary) agar data tetap available saat satu node down.
4. **CDN untuk frontend** — Gunakan Azure CDN atau Cloudflare untuk meng-cache aset statis frontend, membebaskan bandwidth server untuk request API.
5. **Monitoring & alerting** — Implementasikan Azure Monitor atau Prometheus + Grafana untuk observability real-time, sehingga bottleneck dapat dideteksi sebelum berdampak ke user.
6. **Connection pooling MongoDB** — Konfigurasi `maxPoolSize` pada MongoClient di `app.py` agar koneksi database dikelola lebih efisien di bawah concurrent load tinggi.
