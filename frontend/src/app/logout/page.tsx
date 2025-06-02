"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function LogoutPage() {
  const router = useRouter()

  useEffect(() => {
    // 1. Supprimer localStorage
    localStorage.clear()

    // 2. Supprimer les cookies
    document.cookie = "access_token=; path=/; max-age=0"
    document.cookie = "refresh_token=; path=/; max-age=0"

    // 3. Redirection
    router.replace("/login")
  }, [router])

  return null // ou un petit message "Déconnexion en cours..."
}
