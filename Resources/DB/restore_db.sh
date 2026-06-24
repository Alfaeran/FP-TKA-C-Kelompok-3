#!/bin/bash
# Script untuk melakukan restore MongoDB ke VM Database
# Pastikan folder 'dump' sudah ada di direktori yang sama atau jalankan 'python generate_dump.py' terlebih dahulu.

DB_IP="10.0.0.5"
DB_PORT="27017"
DUMP_DIR="dump/"

echo "Memulai proses restore ke MongoDB di ${DB_IP}:${DB_PORT}..."

if [ ! -d "$DUMP_DIR" ]; then
  echo "Error: Folder dump/ tidak ditemukan!"
  echo "Silakan jalankan 'python3 generate_dump.py' terlebih dahulu untuk membuat data dump."
  exit 1
fi

mongorestore --uri="mongodb://${DB_IP}:${DB_PORT}" --drop ${DUMP_DIR}

if [ $? -eq 0 ]; then
  echo "✅ Restore database berhasil!"
else
  echo "❌ Terjadi kesalahan saat melakukan restore."
fi
