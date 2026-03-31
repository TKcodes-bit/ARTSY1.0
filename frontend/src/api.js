import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://localhost:4000";
const normalizedBaseUrl = API_BASE_URL.replace(/\/+$/, "");

const api = axios.create({
  baseURL: `${normalizedBaseUrl}/api`
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

