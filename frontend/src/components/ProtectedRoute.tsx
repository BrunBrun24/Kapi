import React, { useState, useEffect } from "react";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import api from "../api";
import { REFRESH_TOKEN, ACCESS_TOKEN } from "../constants";

// Définition des props : `children` est obligatoire ici
interface ProtectedRouteProps {
  children: ReactNode;
}

// Composant typé avec React.FC
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // État pour suivre l'autorisation de l'utilisateur
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  // Fonction exécutée à la première montée du composant
  useEffect(() => {
    auth().catch(() => setIsAuthorized(false));
  }, []);

  // Fonction pour rafraîchir le token si nécessaire
  const refreshToken = async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN);
    try {
      const res = await api.post("/api/token/refresh/", {
        refresh: refreshToken,
      });
      if (res.status === 200) {
        localStorage.setItem(ACCESS_TOKEN, res.data.access);
        setIsAuthorized(true);
      } else {
        setIsAuthorized(false);
      }
    } catch (error) {
      console.error(error);
      setIsAuthorized(false);
    }
  };

  // Fonction principale d'authentification
  const auth = async () => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    if (!token) {
      setIsAuthorized(false);
      return;
    }

    // Décodage du token JWT pour vérifier la validité
    const decoded: { exp: number } = jwtDecode(token);
    const tokenExpiration = decoded.exp;
    const now = Date.now() / 1000;

    if (tokenExpiration < now) {
      await refreshToken();
    } else {
      setIsAuthorized(true);
    }
  };

  // Affichage pendant la vérification
  if (isAuthorized === null) {
    return <div>Loading...</div>;
  }

  // Redirection ou rendu des enfants selon l'autorisation
  return isAuthorized ? children : <Navigate to="/login" />;
};

export default ProtectedRoute;
