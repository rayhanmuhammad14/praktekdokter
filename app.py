from flask import Flask, render_template, url_for, session, redirect, request
from pymongo import MongoClient
from backend.auth import login
from datetime import timedelta, datetime
from bson import ObjectId

app = Flask(__name__, template_folder='templates')
app.secret_key = "sulianti123"
app.permanent_session_lifetime = timedelta(days=1)
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
        

        pipeline = [
            {
                "$addFields": {
                    "expire": {"$toDate": "$expire"}  
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
                    "selisih_hari": {"$lte": 90}  
                }
            },
            {
                "$project": {
                    "kode": 1,  
                    "selisih_hari": 1
                }
            }
        ]

        dataKartu = list(collectionKartu.aggregate(pipeline))

        kode_list = [doc["kode"] for doc in dataKartu if "kode" in doc]

        if kode_list and isinstance(kode_list[0], str):
            try:
                kode_list = [ObjectId(k) for k in kode_list]
            except:
                pass

        nama_obat_list = []
        if kode_list:
            nama_obat_cursor = collectionObat.find(
                {"_id": {"$in": kode_list}},  
                {"nama": 1, "_id": 0}  
            )
            nama_obat_list = [doc["nama"] for doc in nama_obat_cursor]

        if nama_obat_list:
            div = "danger"
            msg = f"⚠️ OBAT {', '.join(nama_obat_list)} sudah mendekati kedaluwarsa! Tolong periksa stok."
        else:
            div = "success"
            msg = "✅ Semua obat aman, tidak ada yang mendekati kedaluwarsa."
            
        per_page = 100
        page = int(request.args.get('page', 1))
        skip = (page - 1) * per_page
        if search_query:
            total_obat = collectionObat.count_documents({"nama": {"$regex": search_query, "$options": "i"}})
            obat_cursor = collectionObat.find({"nama": {"$regex": search_query, "$options": "i"}}).skip(skip).limit(per_page)
        else:
            total_obat = collectionObat.count_documents({})
            obat_cursor = collectionObat.find().skip(skip).limit(per_page)
            
        obat_list = list(obat_cursor)
        total_pages = (total_obat + per_page - 1) // per_page
        return render_template(
            'home.html',
            obat_list=obat_list,
            msg=msg,
            div=div,
            total_pages=total_pages,
            current_page=page,
            search_query=search_query,
            page=page,
            per_page=per_page
        )
    else:
        return redirect(url_for('index'))

@app.route('/addObat', methods = ['POST'])
def addObat():
    if "user" in session:
        nama = request.form['namaObat']
        satuan = request.form['satuan']
        harga = request.form['harga']

        collectionObat.insert_one({'nama':nama, 'satuan':satuan,'harga':harga})
        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

@app.route('/kartuStok/<obat_id>', methods = ['POST', 'GET'])
def kartuStok(obat_id):
    if "user" in session:
        idBrg = str(obat_id)
        kode = str(obat_id)
        data = list(collectionObat.find({'_id': ObjectId(obat_id)}))
        month_str = str(request.form.get("month", "").strip())

        latest_stok = collectionKartu.find_one({'kode': kode}, {"sisa": 1}, sort=[("_id", -1)])
        stok_terakhir = latest_stok.get("sisa", 0) if latest_stok else "Tidak Ada Stok"
        
        today = datetime.utcnow()
        pipeline = [
            {
                "$match": {"kode": obat_id}
            },
            {
                "$addFields": {
                    "expire": {"$toDate": "$expire"} 
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
                    "_id" : 1,
                    "kode" : 1,
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
        
        pipelineF = [
            {
                "$match": {
                    "kode": obat_id,
                    "tanggal": {"$regex": f"^{month_str}"}  # Cocokkan awal string dengan YYYY-MM
                        }
                    },
                    {
                        "$addFields": {
                            "expire": {"$toDate": "$expire"}
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
                    "_id": 1,
                    "kode": 1,
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

        
        if month_str:
            dataKartu = list(collectionKartu.aggregate(pipelineF))
        else:
            dataKartu = list(collectionKartu.aggregate(pipeline))
        #####
        masuk = collectionKartu.find({'kode':obat_id},{"masuk": 1})
        keluar = collectionKartu.find({'kode':obat_id},{"keluar": 1})
        
        total_masuk = sum(int(d.get("masuk", 0)) for d in masuk)
        total_keluar = sum(int(d.get("keluar", 0)) for d in keluar)

        stok_terkini = int(total_masuk)-int(total_keluar)
        if stok_terkini <= 0:
            stok_terkini = 0

        return render_template(
            'kartuStok.html',
            data_obat=data,
            dataKartu=dataKartu,
            stok_terakhir=stok_terakhir,
            idBrg=idBrg,
            stok_terkini=stok_terkini
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


        tanggalConvert = datetime.strptime(tanggal,"%Y-%m-%d").date()
        expireConvert = datetime.strptime(expire, '%Y-%m-%d').date()



        collectionKartu.insert_one({'kode' : kode,'tanggal' : str(tanggalConvert), 'dk' : dk, 'masuk' : str(masuk), 
                           'keluar' : str(keluar), 'expire' : str(expireConvert)})
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
        expire = request.form['expire']
        kartu = kartu

        collectionKartu.update_one(
            {"_id": ObjectId(kartuId)},
            {"$set": {"tanggal": tanggal, "dk": dk, "masuk": masuk, "keluar":keluar, 'expire': expire}}
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
    app.run('0.0.0.0',debug=True)
