import React from "react";

import PortfolioSelector from "@/components/transaction/portfolio-selector";
import SideBar from "@/app/sidebar/side-bar";

export default function Dashboard() {
  return (
    <div>
      <SideBar>
        <PortfolioSelector />
      </SideBar>
    </div>
  );
}
