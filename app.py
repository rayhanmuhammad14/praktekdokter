from flask import Flask, render_template, url_for, session, redirect, request
from pymongo import MongoClient
from backend.auth import login
from datetime import timedelta, datetime
from bson import ObjectId

app = Flask(__name__, template_folder='templates')
app.secret_key = "sulianti123"
app.permanent_session_lifetime = timedelta(minutes=5)
client = MongoClient("mongodb+srv://rayhan123:kHQ56sgTV1BpgLL3@kartustok.lq6vs.mongodb.net/?retryWrites=true&w=majority&appName=kartuStok")
db = client['kartuStok']
collection = db['kartustok']
collectionObat = db['obat']
collectionKartu = db['kartu']

@app.route('/', methods = ["POST", "GET"])
def index():
    return login(collection)

@app.route('/home', methods = ['GET'])
def home():
   if "user" in session:
    if request.method == 'GET':
        search_query = request.args.get("search", "").strip()
        today = datetime.utcnow()

        # Pipeline untuk menghitung selisih hari sebelum kedaluwarsa
        pipeline = [
            {
                "$addFields": {
                    "expire": {"$toDate": "$expire"}  # Konversi string ke datetime
                }
            },
            {
                "$addFields": {
                    "selisih_hari": {
                        "$dateDiff": {
                            "startDate": today,
                            "endDate": "$expire",
                            "unit": "day"
                        }
                    }
                }
            },
            {
                "$match": {
                    "selisih_hari": {"$lte": 90}  # Filter yang kurang dari 90 hari
                }
            },
            {
                "$project": {
                    "kode": 1,  # Ambil kode obat untuk dicocokkan di collectionObat
                    "selisih_hari": 1
                }
            }
        ]

        # Eksekusi pipeline untuk mendapatkan daftar kartu yang kedaluwarsa dalam ≤90 hari
        dataKartu = list(collectionKartu.aggregate(pipeline))

        # Ambil semua kode obat dari kartu stok
        kode_list = [doc["kode"] for doc in dataKartu if "kode" in doc]

        # Pastikan kode berbentuk ObjectId jika perlu
        if kode_list and isinstance(kode_list[0], str):
            try:
                kode_list = [ObjectId(k) for k in kode_list]
            except:
                pass

        # Ambil nama obat berdasarkan kode yang ditemukan dalam kartu stok
        nama_obat_list = []
        if kode_list:
            nama_obat_cursor = collectionObat.find(
                {"_id": {"$in": kode_list}},  # Cari berdasarkan _id obat
                {"nama": 1, "_id": 0}  # Hanya ambil nama obat
            )
            nama_obat_list = [doc["nama"] for doc in nama_obat_cursor]

        # Tentukan pesan berdasarkan hasil pencarian obat kadaluarsa
        if nama_obat_list:
            div = "danger"
            msg = f"⚠️ OBAT {', '.join(nama_obat_list)} sudah mendekati kedaluwarsa! Tolong periksa stok."
        else:
            div = "success"
            msg = "✅ Semua obat aman, tidak ada yang mendekati kedaluwarsa."

        # Pencarian obat berdasarkan nama
        if search_query:
            obat_list = list(collectionObat.find({"nama": {"$regex": search_query, "$options": "i"}}))
        else:
            obat_list = list(collectionObat.find())

        return render_template('home.html', obat_list=obat_list, msg=msg, div=div)

    else:
        return redirect(url_for('index'))

@app.route('/addObat', methods = ['POST'])
def addObat():
    if "user" in session:
        nama = request.form['namaObat']
        satuan = request.form['satuan']
        harga = request.form['harga']

        collectionObat.insert_one({'nama':nama, 'satuan':satuan,'harga':harga})
        msg = 'berhasil'
        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

@app.route('/kartuStok/<obat_id>', methods = ['POST', 'GET'])
def kartuStok(obat_id):
    if "user" in session:
        idBrg = str(obat_id)
        kode = str(obat_id)

        # Ambil data obat berdasarkan ID
        data = list(collectionObat.find({'_id': ObjectId(obat_id)}))

        # Ambil filter bulan & tahun dari form (jika ada)
        month_str = str(request.form.get("month", "").strip())
        query = {"kode": kode}

        if month_str:
            try:
                # Filter hanya jika user memilih bulan & tahun
                query["tanggal"] = {"$regex": f"^{month_str}"}
            except ValueError:
                pass  # Abaikan jika format salah

        # Ambil data kartu stok (terfilter atau tidak)
        dataKartu = list(collectionKartu.find(query))

        # Ambil stok terakhir
        latest_stok = collectionKartu.find_one({'kode': kode}, {"sisa": 1}, sort=[("_id", -1)])
        stok_terakhir = latest_stok.get("sisa", 0) if latest_stok else "Tidak Ada Stok"
        
        today = datetime.utcnow()
        pipeline = [
            {
                "$match": {"kode": obat_id}
            },
            {
                "$addFields": {
                    "expire": {"$toDate": "$expire"}  # Konversi string ke datetime
                }
            },
            {
                "$addFields": {
                    "selisih_hari": {
                        "$dateDiff": {
                            "startDate": today,
                            "endDate": "$expire",
                            "unit": "day"
                        }
                    }
                }
            },
            {
                "$project": {
                    "tanggal": 1,
                    "dk": 1,
                    "masuk": 1,
                    "keluar": 1,
                    "sisa": 1,
                    "expire": 1,
                    "selisih_hari": 1
                }
            }
        ]

        dataKartu = list(collectionKartu.aggregate(pipeline))

        return render_template(
            'kartuStok.html',
            data_obat=data,
            dataKartu=dataKartu,
            stok_terakhir=stok_terakhir,
            idBrg=idBrg,
            selected_month=month_str  # Kirim bulan yang dipilih ke template
        )

    else:
        return redirect(url_for('index'))


@app.route('/addKartuStok/<obat_id>', methods = ['POST'])
def addKartuStok(obat_id):
    if "user" in session:
        kode = obat_id
        tanggal = request.form['tanggal']
        dk = request.form['dk']
        masuk = int(request.form['masuk'])
        keluar = int(request.form['keluar'])
        expire = request.form['expire']


        today = datetime.today().date()

        tanggalConvert = datetime.strptime(tanggal,"%Y-%m-%d").date()
        expireConvert = datetime.strptime(expire, '%Y-%m-%d').date()

        selisih = (expireConvert - today).days
            

        latest_entry = collectionKartu.find_one({'kode': kode}, {"sisa": 1}, sort=[("_id", -1)])
        if latest_entry:
            sisa_sebelumnya = int(latest_entry["sisa"])
            sisa_baru = sisa_sebelumnya + masuk - keluar
        else:
            sisa_baru = masuk


        collectionKartu.insert_one({'kode' : kode,'tanggal' : str(tanggalConvert), 'dk' : dk, 'masuk' : str(masuk), 
                           'keluar' : str(keluar), 'sisa' : str(sisa_baru), 'expire' : str(expireConvert), 'selisih' : selisih})
        obat_id = kode
        return redirect(url_for('kartuStok', obat_id=obat_id))
    else:
        return redirect(url_for('index'))

@app.route('/updateKartu/<kartuId>/<kartu>', methods = ['POST'])
def updateKartu(kartuId, kartu):
    if "user" in session:
        tanggal = request.form['tanggal']
        dk = request.form['dk']
        masuk = request.form['masuk']
        keluar = request.form['keluar']
        sisa = request.form['sisa']
        expire = request.form['expire']
        kartu = kartu

        collectionKartu.update_one(
            {"_id": ObjectId(kartuId)},
            {"$set": {"tanggal": tanggal, "dk": dk, "masuk": masuk, "keluar":keluar, "sisa":sisa, 'expire': expire}}
        )

        return redirect(url_for('kartuStok', obat_id=kartu))
    else:
        return redirect(url_for('index'))

@app.route('/updateObat/<obatId>', methods = ['POST'])
def updateObat(obatId):
    if "user" in session:
        nama = request.form['namaObat']
        satuan = request.form['satuan']
        harga = request.form['harga']

        collectionObat.update_one(
            {"_id": ObjectId(obatId)},
            {"$set": {"nama": nama, "satuan": satuan, "harga": harga}}
        )

        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

@app.route("/delete/<id>/<kode>")
def delete(id, kode):
    if "user" in session:
        collectionKartu.delete_one({"_id": ObjectId(id)})
        kode = kode
        return redirect(url_for("kartuStok", obat_id=kode))
    else:
        return redirect(url_for('index'))

@app.route("/deleteObat/<id>")
def deleteObat(id):
    if "user" in session:
        collectionObat.delete_one({"_id": ObjectId(id)})
        collectionKartu.delete_many({"kode": id})
        return redirect(url_for("home"))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
