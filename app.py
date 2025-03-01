from flask import Flask, render_template, url_for, session, redirect, request
from pymongo import MongoClient
from backend.auth import login
from datetime import timedelta, datetime
from bson import ObjectId

app = Flask(__name__, template_folder='templates')
app.secret_key = "sulianti123"
app.permanent_session_lifetime = timedelta(minutes=5)
client = MongoClient("mongodb+srv://rayhan123:m5VnblcoXTtzOhUh@kartustok.lq6vs.mongodb.net/?retryWrites=true&w=majority&appName=kartuStok")
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

            if search_query:
                obat_list = list(collectionObat.find({"nama": {"$regex": search_query, "$options": "i"}}))
            else:
                obat_list = list(collectionObat.find())
            return render_template('home.html', obat_list=obat_list)
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

@app.route('/kartuStok/<obat_id>')
def kartuStok(obat_id):
    if "user" in session:
        idBrg = str(obat_id)
        kode = str(obat_id)

        # Ambil data obat berdasarkan ID
        data = list(collectionObat.find({'_id': ObjectId(obat_id)}))

        # Ambil data kartu stok berdasarkan kode obat
        dataKartu = list(collectionKartu.find({'kode': kode}))

        # Ambil stok terakhir dari kartu stok
        latest_stok = collectionKartu.find_one({'kode': kode}, {"sisa": 1}, sort=[("_id", -1)])
    
        if latest_stok:
            stok_terakhir = latest_stok.get("sisa", 0)
        else:
            stok_terakhir = "Tidak Ada Stok"

        return render_template('kartuStok.html', data_obat=data, dataKartu=dataKartu, stok_terakhir=stok_terakhir, idBrg=idBrg)
    
    else:
        return redirect(url_for('index'))


@app.route('/addKartuStok/<obat_id>', methods = ['POST'])
def addKartuStok(obat_id):
    if "user" in session:
        kode = obat_id
        tanggal = request.form['tanggal']
        dk = request.form['dk']
        masuk = request.form['masuk']
        keluar = request.form['keluar']
        sisa = request.form['sisa']
        expire = request.form['expire']

        today = datetime.today().date()

        tanggalConvert = datetime.strptime(tanggal,"%Y-%m-%d").date()
        expireConvert = datetime.strptime(expire, '%Y-%m-%d').date()

        selisih = (expireConvert - today).days

        collectionKartu.insert_one({'kode' : kode,'tanggal' : str(tanggalConvert), 'dk' : dk, 'masuk' : str(masuk), 
                           'keluar' : str(keluar), 'sisa' : str(sisa), 'expire' : str(expireConvert), 'selisih' : selisih})
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
