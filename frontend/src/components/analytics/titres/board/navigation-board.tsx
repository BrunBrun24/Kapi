import { BoardPositionsTickers } from "@/components/analytics/titres/board/positions/board-position-tickers";
import { BoardAllTransactions } from "@/components/analytics/titres/board/transactions/board-ticker-transaction";
import { IconStackFront } from "@tabler/icons-react";
import { List } from "lucide-react";
import React, { useState } from "react";
import { SelectedPortfolio } from "../../type";

export const NavBar = ({ selectedPortfolio }: SelectedPortfolio) => {
  const [activeTab, setActiveTab] = useState<"positions" | "transactions">(
    "positions"
  );

  const tabClasses = (isActive: boolean) =>
    `flex items-center gap-1.5 cursor-pointer font-bold pb-1 
     ${isActive ? "text-blue-600 border-b-2 border-blue-600" : "text-black"}`;

  return (
    <div>
      <nav className="flex gap-5">
        <div
          role="button"
          tabIndex={0}
          onClick={() => setActiveTab("positions")}
          className={tabClasses(activeTab === "positions")}
        >
          <IconStackFront size={20} /> Positions
        </div>
        <div
          role="button"
          tabIndex={0}
          onClick={() => setActiveTab("transactions")}
          className={tabClasses(activeTab === "transactions")}
        >
          <List size={20} /> Transactions
        </div>
      </nav>

      <div className="mt-5">
        {activeTab === "positions" ? (
          <BoardPositionsTickers selectedPortfolio={selectedPortfolio} />
        ) : (
          <BoardAllTransactions selectedPortfolio={selectedPortfolio} />
        )}
      </div>
    </div>
  );
};
