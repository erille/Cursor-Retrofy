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
import bcrypt
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()


# Configuration
DB_PATH = os.environ.get("DB_PATH", "/srv/sqlite/ma_base.sqlite")
IMAGES_DIR = os.environ.get("IMAGES_DIR", os.path.join(os.getcwd(), "images"))
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-secret-key")

# User authentication configuration
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

# Generate a default password hash if none is provided
if not ADMIN_PASSWORD_HASH:
    # Default password: "admin123" - CHANGE THIS IN PRODUCTION!
    default_password = "admin123"
    salt = bcrypt.gensalt()
    ADMIN_PASSWORD_HASH = bcrypt.hashpw(default_password.encode('utf-8'), salt).decode('utf-8')

# Spotify configuration
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")


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


def get_artist_info(db: sqlite3.Connection, artist_id: int) -> Optional[sqlite3.Row]:
    if not artist_id:
        return None
    cur = db.execute("SELECT * FROM artistes WHERE id = ?", (artist_id,))
    return cur.fetchone()


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


def get_genres_with_counts(db: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = db.execute(
        """
        SELECT genre, COUNT(*) AS num_records
        FROM records
        WHERE genre IS NOT NULL AND TRIM(genre) <> ''
        GROUP BY genre
        ORDER BY num_records DESC, LOWER(genre) ASC
        """
    )
    return cur.fetchall()


def get_years_with_counts(db: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = db.execute(
        """
        SELECT year, COUNT(*) AS num_records
        FROM records
        WHERE year IS NOT NULL AND TRIM(CAST(year AS TEXT)) <> ''
        GROUP BY year
        ORDER BY year DESC
        """
    )
    return cur.fetchall()


def get_latest_records(db: sqlite3.Connection, limit: int = 8) -> List[sqlite3.Row]:
    cur = db.execute(
        """
        SELECT * FROM records
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,)
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


def search_spotify_album(artist: str, album_title: str) -> Optional[Dict[str, Any]]:
    """Search for an album on Spotify and return its information."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    
    try:
        # Initialize Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Search for the album
        query = f"artist:{artist} album:{album_title}"
        results = sp.search(q=query, type='album', limit=1)
        
        if results['albums']['items']:
            album = results['albums']['items'][0]
            return {
                'id': album['id'],
                'name': album['name'],
                'artist': album['artists'][0]['name'] if album['artists'] else '',
                'external_url': album['external_urls']['spotify'],
                'images': album['images']
            }
    except Exception as e:
        # Log error but don't crash the application
        print(f"Spotify search error: {e}")
        return None
    
    return None


def is_logged_in() -> bool:
    return session.get("user") == ADMIN_USERNAME


def login_required() -> None:
    if not is_logged_in():
        abort(403)


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_sidebar_data():
        try:
            artists = get_artists_with_counts(g.db)
            genres = get_genres_with_counts(g.db)
            years = get_years_with_counts(g.db)
        except Exception:  # noqa: BLE001
            artists = []
            genres = []
            years = []
        return dict(artist_counts=artists, genre_counts=genres, year_counts=years)

    @app.get("/")
    def index():
        q = request.args.get("q")
        artist = request.args.get("artist")
        year = request.args.get("year")
        genre = request.args.get("genre")
        
        # Check if any search filters are active
        has_filters = any([q, artist, year, genre])
        
        if has_filters:
            records = query_records(g.db, q=q, artist=artist, year=year, genre=genre)
        else:
            # Get last 20 records added
            records = get_latest_records(g.db, limit=20)

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
            is_welcome=not has_filters,
        )

    @app.get("/records/<int:record_id>")
    def record_detail(record_id: int):
        rec = get_record(g.db, record_id)
        img = get_record_image(g.db, record_id)
        artist = get_artist_info(g.db, rec["artiste_id"]) if rec["artiste_id"] else None
        
        # Search for album on Spotify
        spotify_album = search_spotify_album(rec["artist"], rec["album_title"])
        
        return render_template("detail.html", record=rec, image=img, artist=artist, spotify_album=spotify_album)

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
        
        # Check username and password
        if (username == ADMIN_USERNAME and 
            bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8'))):
            session["user"] = ADMIN_USERNAME
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
        
        # Define allowed fields with explicit whitelist to prevent SQL injection
        ALLOWED_FIELDS = {
            "artist": "artist",
            "album_title": "album_title", 
            "year": "year",
            "label": "label",
            "genre": "genre",
            "style": "style",
            "location": "location",
            "notes": "notes",
            "price": "price",
            "currency": "currency",
            "quantity": "quantity",
        }
        
        # Build update clauses safely using whitelisted field names
        update_clauses: List[str] = []
        values: List[Any] = []
        
        for form_field, db_column in ALLOWED_FIELDS.items():
            if form_field in request.form:
                # Only add valid, whitelisted fields to prevent SQL injection
                update_clauses.append(f"{db_column} = ?")
                values.append(request.form.get(form_field))
        
        if update_clauses:
            # Construct the SQL query with whitelisted field names
            sql = "UPDATE records SET " + ", ".join(update_clauses) + ", updated_at = datetime('now') WHERE id = ?"
            values.append(record_id)
            
            try:
                g.db.execute(sql, tuple(values))
                g.db.commit()
                flash("Enregistrement mis à jour.", "success")
            except sqlite3.Error as e:
                g.db.rollback()
                flash(f"Erreur lors de la mise à jour: {str(e)}", "error")
        else:
            flash("Aucun changement détecté.", "warning")
            
        return redirect(url_for("record_detail", record_id=rec["id"]))  # type: ignore[index]


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)


