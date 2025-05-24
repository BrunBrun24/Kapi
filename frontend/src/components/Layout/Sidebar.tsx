import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  LineChart,
  CircleDollarSign,
  Settings,
  ChevronDown,
  TrendingUp,
  PieChart,
  BarChart2,
  Building2,
  LogIn,
  LogOut,
} from "lucide-react";
import "../../static/css/Layout/Sidebar.css";

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
  subItems?: Array<{
    label: string;
    icon: React.ReactNode;
    onClick: () => void;
  }>;
  isOpen?: boolean; // Ajout de l'état d'ouverture du sous-menu
  onToggle?: () => void; // Fonction de bascule pour ouvrir/fermer le sous-menu
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  icon,
  label,
  active,
  onClick,
  subItems,
  isOpen,
  onToggle,
}) => {
  return (
    <div>
      <li
        className={`sidebar-item ${active ? "active" : ""} ${
          isOpen ? "open" : ""
        }`}
        onClick={() => {
          if (subItems) {
            onToggle?.(); // Bascule l'état du sous-menu
          } else if (onClick) {
            onClick();
          }
        }}
      >
        <div className="icon">{icon}</div>
        <span className="label">{label}</span>
        {subItems && <ChevronDown size={16} className="chevron" />}
      </li>

      {isOpen && subItems && (
        <ul className="submenu">
          {subItems.map((item, index) => (
            <li key={index} className="submenu-item" onClick={item.onClick}>
              <span className="icon">{item.icon}</span>
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState("portfolio");
  const [openSubMenu, setOpenSubMenu] = useState<string | null>(null);

  const handleSubItemClick = (section: string, route: string) => {
    setActiveSection(section);
    navigate(route);
  };

  const portfolioSubItems = [
    {
      label: "Dashboard",
      icon: <PieChart size={16} />,
      onClick: () => handleSubItemClick("portfolio", "/portfolio/dashboard"),
    },
    {
      label: "Transactions",
      icon: <BarChart2 size={16} />,
      onClick: () => handleSubItemClick("portfolio", "/portfolio/transactions"),
    },
    {
      label: "Performance",
      icon: <TrendingUp size={16} />,
      onClick: () => handleSubItemClick("portfolio", "/portfolio/performance"),
    },
    {
      label: "Dividends",
      icon: <CircleDollarSign size={16} />,
      onClick: () => handleSubItemClick("portfolio", "/portfolio/dividends"),
    },
  ];

  const analyticsSubItems = [
    {
      label: "Entreprises",
      icon: <Building2 size={16} />,
      onClick: () => handleSubItemClick("analytics", "/portfolio/analytics"),
    },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <BarChart3 className="logo" />
        <h1>StockFolio</h1>
      </div>

      <div className="sidebar-list">
        <ul>
          <SidebarItem
            icon={<BarChart3 size={20} />}
            label="Portfolio"
            active={activeSection === "portfolio"}
            subItems={portfolioSubItems}
            isOpen={openSubMenu === "portfolio"}
            onToggle={() =>
              setOpenSubMenu(openSubMenu === "portfolio" ? null : "portfolio")
            }
          />
          <SidebarItem
            icon={<LineChart size={20} />}
            label="Analytics"
            active={activeSection === "analytics"}
            subItems={analyticsSubItems}
            isOpen={openSubMenu === "analytics"}
            onToggle={() =>
              setOpenSubMenu(openSubMenu === "analytics" ? null : "analytics")
            }
          />
          <SidebarItem
            icon={<Settings size={20} />}
            label="Settings"
            active={activeSection === "settings"}
            onClick={() => {
              setActiveSection("settings");
              setOpenSubMenu(null);
              navigate("/settings");
            }}
          />
          <SidebarItem
            icon={<LogOut size={20} />}
            label="Déconnexion"
            active={activeSection === "logout"}
            onClick={() => {
              setActiveSection("logout");
              setOpenSubMenu(null);
              navigate("/logout");
            }}
          />
          <SidebarItem
            icon={<LogIn size={20} />}
            label="Connexion"
            active={activeSection === "login"}
            onClick={() => {
              setActiveSection("login");
              setOpenSubMenu(null);
              navigate("/login");
            }}
          />
        </ul>
      </div>
    </div>
  );
};

export default Sidebar;
