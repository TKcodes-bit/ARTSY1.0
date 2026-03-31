import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value is not None else default


PORT = int(_env("PORT", "4000"))
JWT_SECRET = _env("JWT_SECRET", "change_this_in_production")
CLIENT_ORIGIN = _env("CLIENT_ORIGIN", "http://localhost:5173")
DATABASE_URL = _env("DATABASE_URL", "sqlite:///artsy.sqlite3")
UPLOAD_FOLDER = _env("UPLOAD_FOLDER", "uploads")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

CORS(app, origins=[CLIENT_ORIGIN])
db = SQLAlchemy(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


conversation_participants = db.Table(
    "conversation_participants",
    db.Column("conversation_id", db.Integer, db.ForeignKey("conversation.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # artist | viewer
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    artist = db.relationship("User")
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(1024), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    participants = db.relationship("User", secondary=conversation_participants, lazy="subquery")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    conversation = db.relationship("Conversation")
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    sender = db.relationship("User")
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


def init_db():
    # Ensure tables exist when running under gunicorn/railway.
    with app.app_context():
        db.create_all()


init_db()


def to_user(u: User):
    return {
        "id": str(u.id),
        "name": u.name,
        "email": u.email,
        "role": u.role,
    }


def to_artwork(a: Artwork):
    return {
        "_id": str(a.id),
        "title": a.title,
        "description": a.description,
        "imageUrls": [a.image_url],
        "createdAt": a.created_at.isoformat(),
        "artist": {
            "_id": str(a.artist.id),
            "name": a.artist.name,
            "role": a.artist.role,
        },
    }


def to_conversation(c: Conversation):
    return {
        "_id": str(c.id),
        "participants": [
            {"_id": str(p.id), "name": p.name, "role": p.role}
            for p in c.participants
        ],
        "updatedAt": c.updated_at.isoformat(),
        "createdAt": c.created_at.isoformat(),
    }


def to_message(m: Message):
    return {
        "_id": str(m.id),
        "text": m.text,
        "createdAt": m.created_at.isoformat(),
        "sender": {
            "_id": str(m.sender.id),
            "name": m.sender.name,
            "role": m.sender.role,
        },
    }


def sign_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"id": str(user.id), "role": user.role, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def auth_required(fn):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing token"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = int(payload["id"])
        except Exception:
            return jsonify({"message": "Invalid token"}), 401

        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"message": "User not found"}), 401

        request.current_user = user
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


@app.get("/")
def root():
    return jsonify({"message": "Artsy API running"})


@app.get("/uploads/<path:filename>")
def serve_upload(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.post("/api/auth/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()

    if not name or not email or not password or role not in ("artist", "viewer"):
        return jsonify({"message": "Missing fields"}), 400

    if db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none() is not None:
        return jsonify({"message": "Email already used"}), 409

    u = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(u)
    db.session.commit()

    token = sign_token(u)
    return jsonify({"token": token, "user": to_user(u)}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    u = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if u is None or not check_password_hash(u.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = sign_token(u)
    return jsonify({"token": token, "user": to_user(u)})


@app.get("/api/artworks")
def list_artworks():
    q = (request.args.get("q") or "").strip()

    stmt = db.select(Artwork).order_by(Artwork.created_at.desc())
    if q:
        stmt = stmt.filter(Artwork.title.ilike(f"%{q}%"))

    artworks = db.session.execute(stmt).scalars().all()
    return jsonify([to_artwork(a) for a in artworks])


@app.post("/api/artworks")
@auth_required
def create_artwork():
    user: User = request.current_user
    if user.role != "artist":
        return jsonify({"message": "Only artists can upload artworks"}), 403

    # Support upload from computer (multipart/form-data)
    if "image" in request.files:
        file = request.files["image"]
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip() or None

        if not title or file is None or file.filename == "":
            return jsonify({"message": "Title and image file required"}), 400

        safe_name = secure_filename(file.filename)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        filename = f"{ts}_{safe_name}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        image_url = f"/uploads/{filename}"

        a = Artwork(
            artist_id=user.id,
            title=title,
            description=description,
            image_url=image_url,
        )
        db.session.add(a)
        db.session.commit()

        return jsonify(to_artwork(a)), 201

    # JSON fallback (paste an image URL)
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip() or None
    image_url = (data.get("imageUrl") or "").strip()

    if not title or not image_url:
        return jsonify({"message": "Title and image URL required"}), 400

    a = Artwork(
        artist_id=user.id,
        title=title,
        description=description,
        image_url=image_url,
    )
    db.session.add(a)
    db.session.commit()

    return jsonify(to_artwork(a)), 201


@app.get("/api/chat/conversations")
@auth_required
def list_conversations():
    user: User = request.current_user
    stmt = (
        db.select(Conversation)
        .join(conversation_participants)
        .where(conversation_participants.c.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convos = db.session.execute(stmt).scalars().all()
    return jsonify([to_conversation(c) for c in convos])


@app.post("/api/chat/conversations")
@auth_required
def create_conversation():
    user: User = request.current_user
    data = request.get_json(force=True, silent=True) or {}
    recipient_id = data.get("recipientId")

    try:
        rid = int(recipient_id)
    except Exception:
        return jsonify({"message": "recipientId required"}), 400

    if rid == user.id:
        return jsonify({"message": "recipientId required"}), 400

    recipient = db.session.get(User, rid)
    if recipient is None:
        return jsonify({"message": "recipientId required"}), 400

    existing = (
        db.session.query(Conversation)
        .filter(Conversation.participants.any(User.id == user.id))
        .filter(Conversation.participants.any(User.id == rid))
        .first()
    )
    if existing:
        return jsonify(to_conversation(existing)), 201

    c = Conversation(updated_at=datetime.now(timezone.utc))
    c.participants.append(user)
    c.participants.append(recipient)
    db.session.add(c)
    db.session.commit()

    return jsonify(to_conversation(c)), 201


@app.get("/api/chat/messages/<conversation_id>")
@auth_required
def list_messages(conversation_id: str):
    user: User = request.current_user
    if not conversation_id.isdigit():
        return jsonify({"message": "Not part of this conversation"}), 403

    convo = db.session.get(Conversation, int(conversation_id))
    if convo is None or all(p.id != user.id for p in convo.participants):
        return jsonify({"message": "Not part of this conversation"}), 403

    stmt = db.select(Message).where(Message.conversation_id == convo.id).order_by(Message.created_at.asc())
    msgs = db.session.execute(stmt).scalars().all()
    return jsonify([to_message(m) for m in msgs])


@app.post("/api/chat/messages/<conversation_id>")
@auth_required
def send_message(conversation_id: str):
    user: User = request.current_user
    if not conversation_id.isdigit():
        return jsonify({"message": "Not part of this conversation"}), 403

    convo = db.session.get(Conversation, int(conversation_id))
    if convo is None or all(p.id != user.id for p in convo.participants):
        return jsonify({"message": "Not part of this conversation"}), 403

    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"message": "Text required"}), 400

    m = Message(conversation_id=convo.id, sender_id=user.id, text=text)
    convo.updated_at = datetime.now(timezone.utc)
    db.session.add(m)
    db.session.add(convo)
    db.session.commit()

    return jsonify(to_message(m)), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=PORT, debug=True)

