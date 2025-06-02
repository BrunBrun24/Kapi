"use client";

import { useState, useEffect } from "react";

import api from "@/api";

export interface Currency {
  code: string;
  label: string;
}

export function useCurrencySearch() {
  const [allCurrencies, setCurrencies] = useState<Currency[]>([]);
  const [searchCurrency, setSearchCurrency] = useState("");
  const [filteredCurrency, setFilteredCurrency] = useState<Currency[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrency = async () => {
      try {
        const res = await api.get(`/api/currencies/`);
        const currencies = res.data;
        setCurrencies(currencies);
      } catch (error) {
        console.error("Erreur lors de la récupération des devises", error);
      }
    };

    fetchCurrency();
  }, []);

  const handleSearchChangeCurrency = (
      e: React.ChangeEvent<HTMLInputElement>
    ) => {
      const query = e.target.value;
      setSearchCurrency(query);
  
      setFilteredCurrency(allCurrencies.slice(0, 10)); // Limiter à 10 résultats
    };

  const handleSelectCurrency = (code: string) => {
    setSelectedCurrency(code);
    setSearchCurrency(code);
    setFilteredCurrency([]);
  };

  return {
    allCurrencies,
    searchCurrency,
    filteredCurrency,
    selectedCurrency,
    handleSearchChangeCurrency,
    handleSelectCurrency,
  };
}
