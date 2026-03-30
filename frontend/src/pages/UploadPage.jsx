import { useState } from "react";
import api from "../api";

export default function UploadPage() {
  const [form, setForm] = useState({
    title: "",
    description: "",
    imageUrl: ""
  });
  const [message, setMessage] = useState("");
  const [file, setFile] = useState(null);

  function onChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (file) {
        const data = new FormData();
        data.append("title", form.title);
        data.append("description", form.description);
        data.append("image", file);
        await api.post("/artworks", data, {
          headers: { "Content-Type": "multipart/form-data" }
        });
      } else {
        await api.post("/artworks", {
          title: form.title,
          description: form.description,
          imageUrl: form.imageUrl
        });
      }
      setMessage("Artwork uploaded.");
      setForm({ title: "", description: "", imageUrl: "" });
      setFile(null);
    } catch (e) {
      setMessage(e.response?.data?.message || "Upload failed");
    }
  }

  return (
    <div className="upload-card">
      <h2>Share your artwork</h2>
      {message && <p>{message}</p>}
      <form onSubmit={handleSubmit}>
        <label>
          Title
          <input name="title" value={form.title} onChange={onChange} required />
        </label>
        <label>
          Description
          <textarea name="description" value={form.description} onChange={onChange} />
        </label>
        <label>
          Upload from computer (single image)
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>
        <label>
          Or paste an Image URL
          <input
            name="imageUrl"
            value={form.imageUrl}
            onChange={onChange}
            placeholder="Paste a single image link (optional if you selected a file)"
          />
        </label>
        <button type="submit">Upload</button>
      </form>
    </div>
  );
}

