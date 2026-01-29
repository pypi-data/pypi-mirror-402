from bah_lol import BahLol

app = BahLol()

@app.barang("/minyak")
def minyak():
    return {
        "status": "mantap",
        "pesan": "Ini BARANG sudah kita kasih paham"
    }

@app.barang("/bbm", method="POST")
def bbm(data):
    return {
        "bbm_masuk": data,
        "catatan": "Kalau input jelas, hasil juga jelas"
    }

@app.barang("/users/<id>")
def get_user(user_id):
    return {
        "user_id": user_id,
        "name": "Sample User",
        "status": "active"
    }

if __name__ == "__main__":
    app.gas()