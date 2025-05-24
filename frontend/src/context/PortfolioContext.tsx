import React, { createContext, useContext, useReducer, useEffect } from "react";
import type {
  Portfolio,
  Transaction,
  PortfolioState,
} from "../components/Portfolio/type";

// Action types
type Action =
  | { type: "SET_PORTFOLIOS"; payload: Portfolio[] }
  | { type: "ADD_PORTFOLIO"; payload: Portfolio }
  | { type: "SELECT_PORTFOLIO"; payload: string }
  | { type: "SET_TRANSACTIONS"; payload: Transaction[] }
  | { type: "ADD_TRANSACTION"; payload: Transaction }
  | { type: "DELETE_TRANSACTION"; payload: string }
  | { type: "EDIT_TRANSACTION"; payload: Transaction };

// Initial state
const initialState: PortfolioState = {
  portfolios: [],
  selectedPortfolioId: null,
  transactions: [],
};

// Create context
const PortfolioContext = createContext<{
  state: PortfolioState;
  dispatch: React.Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => null,
});

// Reducer function
const portfolioReducer = (
  state: PortfolioState,
  action: Action
): PortfolioState => {
  switch (action.type) {
    case "SET_PORTFOLIOS":
      return {
        ...state,
        portfolios: action.payload,
        selectedPortfolioId:
          state.selectedPortfolioId ||
          (action.payload.length > 0 ? action.payload[0].id : null),
      };

    case "ADD_PORTFOLIO":
      return {
        ...state,
        portfolios: [...state.portfolios, action.payload],
        selectedPortfolioId: action.payload.id,
      };

    case "SELECT_PORTFOLIO":
      return {
        ...state,
        selectedPortfolioId: action.payload,
      };

    case "SET_TRANSACTIONS":
      return {
        ...state,
        transactions: action.payload,
      };

    case "ADD_TRANSACTION":
      return {
        ...state,
        transactions: [...state.transactions, action.payload],
      };

    case "DELETE_TRANSACTION":
      return {
        ...state,
        transactions: state.transactions.filter((t) => t.id !== action.payload),
      };

    case "EDIT_TRANSACTION":
      return {
        ...state,
        transactions: state.transactions.map((t) =>
          t.id === action.payload.id ? action.payload : t
        ),
      };

    default:
      return state;
  }
};

// Provider component
export const PortfolioProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(portfolioReducer, initialState);

  // Load data from localStorage when the component mounts
  useEffect(() => {
    const savedPortfolios = localStorage.getItem("portfolios");
    const savedTransactions = localStorage.getItem("transactions");
    const savedSelectedPortfolioId = localStorage.getItem(
      "selectedPortfolioId"
    );

    if (savedPortfolios) {
      dispatch({
        type: "SET_PORTFOLIOS",
        payload: JSON.parse(savedPortfolios),
      });
    }

    if (savedTransactions) {
      dispatch({
        type: "SET_TRANSACTIONS",
        payload: JSON.parse(savedTransactions),
      });
    }

    if (savedSelectedPortfolioId) {
      dispatch({ type: "SELECT_PORTFOLIO", payload: savedSelectedPortfolioId });
    }
  }, []);

  // Save data to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem("portfolios", JSON.stringify(state.portfolios));
    localStorage.setItem("transactions", JSON.stringify(state.transactions));
    if (state.selectedPortfolioId) {
      localStorage.setItem("selectedPortfolioId", state.selectedPortfolioId);
    }
  }, [state]);

  return (
    <PortfolioContext.Provider value={{ state, dispatch }}>
      {children}
    </PortfolioContext.Provider>
  );
};

// Custom hook for using the portfolio context
export const usePortfolio = () => useContext(PortfolioContext);
