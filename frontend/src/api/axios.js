import axios from "axios";
import i18n from "../i18n";
import { clearApiCache } from "../hooks/useApiQuery";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const api = axios.create({ baseURL });

// Attach access token + language to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  config.headers["Accept-Language"] = i18n.language || "uz";
  return config;
});

// Transparent refresh-token rotation on 401
let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem("refresh_token");
    if (error.response?.status === 401 && refresh && !original._retry) {
      original._retry = true;
      try {
        refreshing =
          refreshing ||
          axios.post(`${baseURL}/auth/refresh`, { refresh_token: refresh });
        const { data } = await refreshing;
        refreshing = null;
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (e) {
        refreshing = null;
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        clearApiCache();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
