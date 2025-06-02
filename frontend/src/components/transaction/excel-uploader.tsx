"use client";

import React, { useState, useRef } from "react";
import api from "@/api";
import "@/static/css/components/transaction/excel-uploader.css";

const expectedColumns = [
  "Ticker",
  "Opération",
  "Date de la transaction",
  "Montant de la transaction",
  "Prix de l'action lors de la transaction",
  "Quantité",
  "Frais",
];

type Props = {
  selectedPortfolioId: string;
  onImportSuccess?: () => void;
};

const ExcelUploader: React.FC<Props> = ({
  selectedPortfolioId,
  onImportSuccess,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [errorHtml, setErrorHtml] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("portfolioId", selectedPortfolioId.toString());

    try {
      await api.post("/api/upload-excel/transaction/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setErrorHtml(null); // reset error si succès
      setShowModal(false);
      if (onImportSuccess) onImportSuccess();
    } catch (error: any) {
      if (error.response && error.response.status === 500) {
        // 💥 Si le backend renvoie du HTML (error 500)
        setErrorHtml(error.response.data);
      } else {
        console.error("❌ Erreur lors de l'envoi du fichier Excel", error);
        setErrorHtml(error.response.data);
      }
    } finally {
      e.target.value = "";
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <button
        type="button"
        className="icon-button"
        onClick={() => setShowModal(true)}
        title="Importer un fichier Excel"
      >
        Importer depuis Excel
      </button>

      {showModal && !errorHtml && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button
              className="close-icon"
              onClick={() => setShowModal(false)}
              aria-label="Fermer"
            >
              &times;
            </button>

            <h4>Format attendu du fichier Excel :</h4>
            <table className="excel-table">
              <thead>
                <tr>
                  {expectedColumns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  {expectedColumns.map((_, idx) => (
                    <td key={idx}>...</td>
                  ))}
                </tr>
              </tbody>
            </table>

            <div className="action-buttons">
              <a href="./transaction.xlsx" download className="download-button">
                Télécharger un exemple
              </a>

              <button
                type="button"
                className="import-button"
                onClick={triggerFileInput}
              >
                Importer un fichier Excel
              </button>
              <input
                type="file"
                accept=".xlsx, .xls"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: "none" }}
              />
            </div>
          </div>
        </div>
      )}

      {errorHtml && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button
              className="close-icon"
              onClick={() => {
                setErrorHtml(null);
                setShowModal(false);
              }}
              aria-label="Fermer"
            >
              &times;
            </button>
            <div
              className="error-box"
              dangerouslySetInnerHTML={{ __html: errorHtml }}
            />
          </div>
        </div>
      )}
    </>
  );
};

export default ExcelUploader;
