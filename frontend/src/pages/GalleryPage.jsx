import { useEffect, useState } from "react";
import api from "../api";
import ArtworkCard from "../components/ArtworkCard.jsx";

export default function GalleryPage() {
  const [artworks, setArtworks] = useState([]);
  const [q, setQ] = useState("");

  async function load() {
    const res = await api.get("/artworks", { params: { q } });
    setArtworks(res.data);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <section className="hero">
        <h1>Art of Work for Work</h1>
        <p>
          A bright space for African youth to share, discover, and converse through art – without
          middlemen or transactions.
        </p>
      </section>
      <div className="search-bar">
        <input
          placeholder="Search artworks..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button onClick={load}>Search</button>
      </div>
      <div className="gallery-grid">
        {artworks.map((a) => (
          <ArtworkCard key={a._id} artwork={a} />
        ))}
        {artworks.length === 0 && <p>No artworks yet. Be the first to upload.</p>}
      </div>
    </div>
  );
}

