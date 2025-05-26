import Sidebar from "./Sidebar";
import { Outlet } from "react-router-dom";

import "../../static/css/layout/LayoutWithSidebar.css";

const LayoutWithSidebar = () => (
  <div className="app-container">
    <Sidebar />
    <div className="main-content">
      <Outlet />
    </div>
  </div>
);

export default LayoutWithSidebar;
