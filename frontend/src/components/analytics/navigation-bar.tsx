"use client";

import { useEffect, useState } from "react";
import DashboardPage from "./dashboard/dashborad-page";
import PerformancePage from "@/components/analytics/performance/performance-page";
import TitresPage from "@/components/analytics/titres/titre-page";
import DividendsPage from "@/components/analytics/dividends/dividends-page";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/api";

import {
  portfolioGlobalName,
  type PortfolioData,
  type UserPortfolio,
} from "@/components/analytics/type";

const tabs = [
  { id: "dashboard", label: "Dashboard" },
  { id: "performance", label: "Performance" },
  { id: "titres", label: "Titres" },
  { id: "dividendes", label: "Dividendes" },
];

export function NavigationBar() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dataPortfolio, setDataPortfolio] = useState<
    UserPortfolio[] | undefined
  >();
  const [selectedPortfolio, setSelectedPortfolio] = useState<
    UserPortfolio | undefined
  >();

  useEffect(() => {
    const getUserPortfolioData = async () => {
      try {
        const res = await api.get("api/user/portfolio/");
        const fetchedData = res.data as UserPortfolio[];
        setDataPortfolio(fetchedData);

        const myPortfolio = fetchedData.find(
          (p) => p.name === portfolioGlobalName
        );

        if (myPortfolio) {
          setSelectedPortfolio(myPortfolio);
        }
      } catch (error) {
        console.error(
          "Erreur lors de la récupération des portefeuilles",
          error
        );
      }
    };

    getUserPortfolioData();
  }, []);

  return (
    <div>
      {/* Barre de navigation */}
      <div className="relative border-b border-gray-300">
        <div className="flex justify-between items-center px-4">
          {/* Onglets à gauche */}
          <div className="flex space-x-10">
            {tabs.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`relative pb-3 text-sm font-medium transition-colors ${
                  activeTab === id
                    ? "text-blue-600"
                    : "text-gray-600 hover:text-blue-600"
                }`}
              >
                {label}
                {activeTab === id && (
                  <span className="absolute -bottom-px left-0 right-0 h-[2px] bg-blue-600" />
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {activeTab !== "dashboard" && (
        <div className="p-4">
          <Select
            value={selectedPortfolio?.id}
            onValueChange={(id) => {
              const found = dataPortfolio?.find((p) => p.id === id);
              if (found) setSelectedPortfolio(found);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sélectionner un portefeuille" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Portefeuilles</SelectLabel>

                {/* Tous (My Portfolio) */}
                {dataPortfolio
                  ?.filter((p) => p.name === portfolioGlobalName)
                  .map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      Tous
                    </SelectItem>
                  ))}

                {/* Autres portefeuilles */}
                {dataPortfolio
                  ?.filter((p) => p.name.toLowerCase() !== portfolioGlobalName)
                  .map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Contenu dynamique */}
      <div className="p-4">
        {activeTab === "dashboard" && (
          <DashboardPage selectedPortfolio={selectedPortfolio} />
        )}
        {activeTab === "performance" && (
          <PerformancePage
            selectedPortfolio={selectedPortfolio}
          />
        )}
        {activeTab === "titres" && (
          <TitresPage
            portfolioId={selectedPortfolio}
          />
        )}
        {activeTab === "dividendes" && (
          <DividendsPage
            portfolioId={selectedPortfolio}
          />
        )}
      </div>
    </div>
  );
}
