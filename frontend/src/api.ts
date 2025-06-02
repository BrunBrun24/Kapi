import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "@/constants";
import { isTokenExpired } from "@/jwt";

const fallbackApiUrl = "http://192.168.1.34:8000";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? fallbackApiUrl,
});

api.interceptors.request.use(async (config) => {
  let token = localStorage.getItem(ACCESS_TOKEN);
  const refreshToken = localStorage.getItem(REFRESH_TOKEN);

  // Vérification de l'inactivité
  const lastActivity = localStorage.getItem("last_activity");
  const now = Date.now();
  const MAX_INACTIVITY = 15 * 60 * 1000; // 15 minutes

  if (lastActivity && now - parseInt(lastActivity, 10) > MAX_INACTIVITY) {
    console.warn("⏳ Inactivité détectée : déconnexion");
    localStorage.clear();
    window.location.href = "/login";
    return Promise.reject("Session expirée pour inactivité");
  }

  if (token && isTokenExpired(token) && refreshToken) {
    try {
      const res = await axios.post(`${fallbackApiUrl}/api/token/refresh/`, {
        refresh: refreshToken,
      });
      token = res.data.access;

      if (token) {
        localStorage.setItem(ACCESS_TOKEN, token);
        document.cookie = `access_token=${token}; path=/; secure; SameSite=Lax`;
      }
    } catch (err) {
      localStorage.clear();
      window.location.href = "/login";
      return Promise.reject(err);
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
