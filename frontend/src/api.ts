import axios from "axios";
import { ACCESS_TOKEN } from "@/constants";

const fallbackApiUrl = "http://192.168.1.34:8000";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? fallbackApiUrl,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
