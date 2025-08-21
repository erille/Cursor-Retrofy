import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
import requests


# Configuration
DB_PATH = os.environ.get("DB_PATH", "/srv/sqlite/ma_base.sqlite")
IMAGES_DIR = os.environ.get("IMAGES_DIR", os.path.join(os.getcwd(), "images"))
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-secret-key")


def ensure_directories() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)


def create_app() -> Flask:
    ensure_directories()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=SECRET_KEY,
        DB_PATH=DB_PATH,
        IMAGES_DIR=IMAGES_DIR,
    )

    @app.before_request
    def before_request() -> None:
        g.db = get_db_connection()

    @app.teardown_request
    def teardown_request(exception: Optional[BaseException]) -> None:  # noqa: U100
        db = getattr(g, "db", None)
        if db is not None:
            db.close()

    register_routes(app)
    return app


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_records(
    db: sqlite3.Connection,
    q: Optional[str] = None,
    artist: Optional[str] = None,
    year: Optional[str] = None,
    genre: Optional[str] = None,
    limit: int = 100,
) -> List[sqlite3.Row]:
    sql = "SELECT * FROM records"
    clauses: List[str] = []
    params: List[Any] = []

    if q:
        like = f"%{q}%"
        clauses.append(
            "(artist LIKE ? OR album_title LIKE ? OR label LIKE ? OR genre LIKE ? OR style LIKE ? OR notes LIKE ?)"
        )
        params.extend([like, like, like, like, like, like])
    if artist:
        clauses.append("artist LIKE ?")
        params.append(f"%{artist}%")
    if year:
        clauses.append("year = ?")
        params.append(year)
    if genre:
        clauses.append("genre LIKE ?")
        params.append(f"%{genre}%")

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY artist, year, album_title"
    sql += " LIMIT ?"
    params.append(limit)

    cur = db.execute(sql, params)
    return cur.fetchall()


def get_record(db: sqlite3.Connection, record_id: int) -> sqlite3.Row:
    cur = db.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cur.fetchone()
    if not row:
        abort(404)
    return row


def get_record_image(db: sqlite3.Connection, record_id: int) -> Optional[sqlite3.Row]:
    cur = db.execute(
        "SELECT * FROM record_images WHERE record_id = ? ORDER BY id DESC LIMIT 1",
        (record_id,),
    )
    return cur.fetchone()


def save_record_image(
    db: sqlite3.Connection, record_id: int, filename: str, kind: str = "cover", note: Optional[str] = None
) -> None:
    db.execute(
        "INSERT INTO record_images (record_id, kind, filename, note) VALUES (?, ?, ?, ?)",
        (record_id, kind, filename, note),
    )
    db.commit()


def get_artists_with_counts(db: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = db.execute(
        """
        SELECT artist, COUNT(*) AS num_records
        FROM records
        WHERE artist IS NOT NULL AND TRIM(artist) <> ''
        GROUP BY artist
        ORDER BY num_records DESC, LOWER(artist) ASC
        """
    )
    return cur.fetchall()


def fetch_cover_via_musicbrainz(artist: str, album_title: str) -> Optional[Tuple[str, bytes]]:
    # Try MusicBrainz release-group lookup first
    base = "https://musicbrainz.org/ws/2"
    headers = {"User-Agent": "Retrofy/1.0 (retrofy.local)"}
    q = f"artist:{artist} AND releasegroup:{album_title}"
    try:
        rg_resp = requests.get(
            f"{base}/release-group",
            params={"query": q, "fmt": "json"},
            headers=headers,
            timeout=10,
        )
        rg_resp.raise_for_status()
        data = rg_resp.json()
        groups = data.get("release-groups", [])
        if groups:
            mbid = groups[0]["id"]
            img = fetch_caa_image("release-group", mbid)
            if img:
                return (f"mb_rg_{mbid}.jpg", img)
    except Exception:  # noqa: BLE001
        pass

    # Fallback to release search
    try:
        r_resp = requests.get(
            f"{base}/release",
            params={"query": f"artist:{artist} AND release:{album_title}", "fmt": "json"},
            headers=headers,
            timeout=10,
        )
        r_resp.raise_for_status()
        data = r_resp.json()
        releases = data.get("releases", [])
        if releases:
            mbid = releases[0]["id"]
            img = fetch_caa_image("release", mbid)
            if img:
                return (f"mb_rel_{mbid}.jpg", img)
    except Exception:  # noqa: BLE001
        pass

    return None


def fetch_caa_image(kind: str, mbid: str) -> Optional[bytes]:
    url = f"https://coverartarchive.org/{kind}/{mbid}/front"
    headers = {"User-Agent": "Retrofy/1.0 (retrofy.local)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.content:
            return resp.content
    except Exception:  # noqa: BLE001
        return None
    return None


def save_image_bytes(content: bytes, suggested_name: str, record_id: int) -> str:
    base_name = f"record_{record_id}_" + suggested_name
    safe_name = base_name.replace("/", "_").replace("\\", "_")
    path = os.path.join(IMAGES_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(content)
    return safe_name


def is_logged_in() -> bool:
    return session.get("user") == "legacy_admin"


def login_required() -> None:
    if not is_logged_in():
        abort(403)


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_sidebar_data():
        try:
            artists = get_artists_with_counts(g.db)
        except Exception:  # noqa: BLE001
            artists = []
        return dict(artist_counts=artists)

    @app.get("/")
    def index():
        q = request.args.get("q")
        artist = request.args.get("artist")
        year = request.args.get("year")
        genre = request.args.get("genre")
        records = query_records(g.db, q=q, artist=artist, year=year, genre=genre)

        # Preload image availability flags
        images_map: Dict[int, Optional[str]] = {}
        for r in records:
            img = get_record_image(g.db, r["id"])  # type: ignore[index]
            images_map[r["id"]] = img["filename"] if img else None  # type: ignore[index]

        return render_template(
            "index.html",
            records=records,
            images_map=images_map,
            q=q or "",
            artist=artist or "",
            year=year or "",
            genre=genre or "",
        )

    @app.get("/records/<int:record_id>")
    def record_detail(record_id: int):
        rec = get_record(g.db, record_id)
        img = get_record_image(g.db, record_id)
        return render_template("detail.html", record=rec, image=img)

    @app.post("/records/<int:record_id>/fetch_cover")
    def record_fetch_cover(record_id: int):
        rec = get_record(g.db, record_id)
        if get_record_image(g.db, record_id):
            return redirect(url_for("record_detail", record_id=record_id))
        found = fetch_cover_via_musicbrainz(rec["artist"], rec["album_title"])  # type: ignore[index]
        if found:
            filename, content = found
            saved = save_image_bytes(content, filename, record_id)
            save_record_image(g.db, record_id, saved, kind="cover", note="auto-fetched")
            flash("Pochette ajoutée automatiquement.", "success")
        else:
            flash("Pochette introuvable.", "warning")
        return redirect(url_for("record_detail", record_id=record_id))

    @app.post("/records/<int:record_id>/upload_cover")
    def upload_cover(record_id: int):
        login_required()
        if "cover" not in request.files:
            flash("Fichier manquant.", "error")
            return redirect(url_for("record_detail", record_id=record_id))
        f = request.files["cover"]
        if not f.filename:
            flash("Nom de fichier invalide.", "error")
            return redirect(url_for("record_detail", record_id=record_id))
        content = f.read()
        saved = save_image_bytes(content, f.filename, record_id)
        save_record_image(g.db, record_id, saved, kind="cover", note="uploaded")
        flash("Pochette importée.", "success")
        return redirect(url_for("record_detail", record_id=record_id))

    @app.get("/covers/<path:filename>")
    def serve_cover(filename: str):
        return send_from_directory(IMAGES_DIR, filename)

    @app.get("/login")
    def login_form():
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == "legacy_admin" and password == "REDACTED_PASSWORD":
            session["user"] = "legacy_admin"
            flash("Connecté.", "success")
            return redirect(url_for("index"))
        flash("Identifiants invalides.", "error")
        return redirect(url_for("login_form"))

    @app.post("/logout")
    def logout():
        session.pop("user", None)
        flash("Déconnecté.", "success")
        return redirect(url_for("index"))

    @app.post("/records/<int:record_id>/edit")
    def edit_record(record_id: int):
        login_required()
        rec = get_record(g.db, record_id)
        # Update a subset of fields that are reasonable to edit from a simple form
        fields = [
            "artist",
            "album_title",
            "year",
            "label",
            "genre",
            "style",
            "location",
            "notes",
            "price",
            "currency",
            "quantity",
        ]
        updates: List[str] = []
        values: List[Any] = []
        for f in fields:
            if f in request.form:
                updates.append(f"{f} = ?")
                values.append(request.form.get(f))
        if updates:
            values.append(record_id)
            g.db.execute(
                f"UPDATE records SET {', '.join(updates)}, updated_at = datetime('now') WHERE id = ?",
                tuple(values),
            )
            g.db.commit()
            flash("Enregistrement mis à jour.", "success")
        else:
            flash("Aucun changement détecté.", "warning")
        return redirect(url_for("record_detail", record_id=rec["id"]))  # type: ignore[index]


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)


