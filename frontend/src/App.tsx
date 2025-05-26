import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/ProtectedRoute";
import TransactionsPage from "./pages/TransactionsPage";
import LayoutWithSidebar from "./components/layout/LayoutWithSidebar";
// import { PortfolioProvider } from "./context/PortfolioContext";

function Logout() {
  localStorage.clear();
  return <Navigate to="/login" />;
}

function RegisterAndLogout() {
  localStorage.clear();
  return <Register />;
}

const PortfoliosDashboard = () => <div>Dashbord page en construction</div>;
const PerformancePage = () => <div>Performance page en construction</div>;
const DividendsPage = () => <div>Dividendes page en construction</div>;
const SettingsPage = () => <div>Paramètres de l'application</div>;

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Routes publiques */}
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        <Route path="*" element={<NotFound />} />

        {/* Routes protégées sous layout */}
        <Route
          element={
            <ProtectedRoute>
              <LayoutWithSidebar />
            </ProtectedRoute>
          }
        >
          <Route
            path="/portfolio/dashboard"
            element={<PortfoliosDashboard />}
          />
          <Route
            path="/portfolio/transactions"
            element={<TransactionsPage />}
          />
          <Route path="/portfolio/performance" element={<PerformancePage />} />
          <Route path="/portfolio/dividends" element={<DividendsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
