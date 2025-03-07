
from pymongo import MongoClient

client = MongoClient("mongodb+srv://rayhan123:kHQ56sgTV1BpgLL3@kartustok.lq6vs.mongodb.net/?retryWrites=true&w=majority&appName=kartuStok")
db = client['kartuStok']
collection = db['kartustok']
collectionObat = db['obat']
collectionKartu = db['kartu']

month_str = "2025-2"
query = {"kode": "67c9916ff61874cf9e12d945"}
if month_str:
            try:
                # Filter hanya jika user memilih bulan & tahun
                query["tanggal"] = {"$regex": f"^{month_str}"}
            except ValueError:
                pass  # Abaikan jika format salah

        # Ambil data kartu stok (terfilter atau tidak)
bulanFilter = list(collectionKartu.find(query))

print (bulanFilter)
