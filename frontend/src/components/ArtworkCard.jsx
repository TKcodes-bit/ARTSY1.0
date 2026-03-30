import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ArtworkCard({ artwork }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const img = artwork.imageUrls?.[0];
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:4000";

  // Backend may return image paths like "/uploads/filename.jpg".
  // Prefix them with the API origin so the browser loads from backend, not frontend.
  const resolvedImg =
    img && typeof img === "string" && img.startsWith("/")
      ? `${API_BASE_URL}${img}`
      : img;

  async function startConversation() {
    if (!user) {
      navigate("/login");
      return;
    }
    const artistId = artwork.artist?._id;
    if (!artistId) return;
    // Reuse or create a conversation with this artist
    const { default: api } = await import("../api.js");
    await api.post("/chat/conversations", { recipientId: artistId });
    navigate("/chat");
  }

  return (
    <div className="art-card">
      <div className="art-3d-container">
        {resolvedImg ? (
          <div className="art-3d-view">
            <img src={resolvedImg} alt={artwork.title} />
          </div>
        ) : (
          <div className="art-placeholder">No image</div>
        )}
      </div>
      <h3>{artwork.title}</h3>
      <p className="artist-name">{artwork.artist?.name}</p>
      <p className="art-desc">{artwork.description}</p>
      {artwork.artist && artwork.artist._id !== user?.id && (
        <button className="chat-artist-btn" onClick={startConversation}>
          Chat with artist about this piece
        </button>
      )}
    </div>
  );
}

