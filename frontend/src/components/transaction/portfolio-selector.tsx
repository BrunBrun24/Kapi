"use client";

import React, { useEffect, useState } from "react";
import { Trash2, Edit, PlusCircle } from "lucide-react";
import Swal from "sweetalert2";

import api from "@/api";
import PortfolioTickers from "./portfolio-tickers";
import type { Portfolio } from "@/components/transaction/type/index";

import "@/static/css/components/transaction/portfolio-selector.css";
import "@/static/css/components/transaction/form.css";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";

const PortfolioSelector: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(
    null
  );
  const [isCreating, setIsCreating] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [portfolioToDelete, setPortfolioToDelete] = useState<Portfolio | null>(
    null
  );

  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        const res = await api.get("/api/portfolios/");
        const userPortfolios = res.data;
        setPortfolios(userPortfolios);
        if (userPortfolios.length > 0) {
          setSelectedPortfolioId(userPortfolios[0].id);
        }
      } catch (error) {
        console.error(
          "Erreur lors de la récupération des portefeuilles",
          error
        );
      }
    };

    fetchPortfolios();
  }, []);

  const handleSelectPortfolio = (id: string) => {
    setSelectedPortfolioId(id);
  };

  const handleCreatePortfolio = async () => {
    if (newPortfolioName.trim() === "") return;

    const newPortfolioData = {
      name: newPortfolioName.trim(),
    };

    try {
      const res = await api.post("/api/portfolios/", newPortfolioData);
      const newPortfolio: Portfolio = res.data;
      const updated = [...portfolios, newPortfolio];
      setPortfolios(updated);
      setSelectedPortfolioId(newPortfolio.id);
      setNewPortfolioName("");
      setIsCreating(false);
    } catch (error) {
      console.error("Erreur lors de la création du portefeuille", error);
    }
  };

  const confirmDeletePortfolio = async () => {
    if (!portfolioToDelete) return;

    try {
      await api.delete(`/api/portfolios/${portfolioToDelete.id}/`);
      setPortfolios((prev) =>
        prev.filter((p) => p.id !== portfolioToDelete.id)
      );
      setSelectedPortfolioId(null);
    } catch (error) {
      console.error("Erreur lors de la suppression du portefeuille", error);
      // Tu peux afficher un toast ici si tu veux
    } finally {
      setPortfolioToDelete(null); // Fermer la modale
    }
  };

  const handleEditPortfolio = async (id: string, currentName: string) => {
    const { value: formValues } = await Swal.fire({
      title: "Modifier le nom du portefeuille",
      html: `<input id="swal-input1" class="swal2-input" placeholder="Nom du portefeuille" value="${currentName}">`,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: "Enregistrer",
      cancelButtonText: "Annuler",
      preConfirm: () => {
        const name = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        if (!name) {
          Swal.showValidationMessage("Tous les champs sont requis");
          return;
        }
        return { name };
      },
    });

    if (formValues) {
      try {
        const response = await api.put(`/api/portfolios/${id}/`, {
          name: formValues.name,
        });

        const updatedPortfolio = response.data;
        setPortfolios((prev) =>
          prev.map((p) => (p.id === id ? updatedPortfolio : p))
        );

        Swal.fire({
          title: "Modifié !",
          text: "Le portefeuille a été mis à jour.",
          icon: "success",
        });
      } catch (error) {
        console.error("Erreur lors de la mise à jour", error);
        Swal.fire({
          title: "Erreur",
          text: "Impossible de modifier le portefeuille.",
          icon: "error",
        });
      }
    }
  };

  return (
    <>
      <div className="portfolio-container">
        <div className="portfolio-heading">
          <h2 className="form-title">Portefeuilles</h2>
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="form-toggle"
          >
            {isCreating ? (
              "Retour"
            ) : (
              <div className="form-toggle-content">
                <PlusCircle size={18} className="form-icon" />
                <span>Nouveau portefeuille</span>
              </div>
            )}
          </button>
        </div>

        {portfolios.length === 0 && !isCreating ? (
          <div className="portfolio-empty">
            <p className="portfolio-empty-text">
              Vous n'avez pas encore de portefeuille
            </p>
          </div>
        ) : (
          <>
            {!isCreating ? (
              <div className="portfolio-list">
                {portfolios.map((portfolio) => (
                  <div
                    key={portfolio.id}
                    className={`portfolio-item ${
                      selectedPortfolioId === portfolio.id
                        ? "portfolio-item--selected"
                        : "portfolio-item--hoverable"
                    }`}
                    onClick={() => handleSelectPortfolio(portfolio.id)}
                  >
                    <div>
                      <h3 className="portfolio-name">{portfolio.name}</h3>
                    </div>

                    <div className="portfolio-actions">
                      <button
                        className="portfolio-edit-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditPortfolio(portfolio.id, portfolio.name);
                        }}
                      >
                        <Edit size={16} />
                      </button>

                      <button
                        className="portfolio-delete-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setPortfolioToDelete(portfolio);
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <form onSubmit={handleCreatePortfolio} className="form-fields">
                <div className="form-block">
                  <div>
                    <label className="form-label">Nom du portefeuille</label>
                    <input
                      type="text"
                      value={newPortfolioName}
                      onChange={(e) => setNewPortfolioName(e.target.value)}
                      placeholder="Entrez un nom de portefeuille"
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <div className="form-submit">
                  <button type="submit" className="form-button">
                    Ajouter un portefeuille
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </div>

      <PortfolioTickers selectedPortfolioId={selectedPortfolioId} />

      {portfolioToDelete && (
        <AlertDialog
          open={!!portfolioToDelete}
          onOpenChange={(open) => {
            if (!open) setPortfolioToDelete(null);
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
              <AlertDialogDescription>
                ⚠️ Cette action est irréversible. Toutes les transactions liées
                à ce portefeuille seront supprimées.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel style={{ cursor: "pointer" }}>
                Annuler
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeletePortfolio}
                style={{ cursor: "pointer" }}
              >
                Oui, supprimer
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </>
  );
};

export default PortfolioSelector;
