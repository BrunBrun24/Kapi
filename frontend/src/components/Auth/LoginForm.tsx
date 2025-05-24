import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../../constants";
import LoadingIndicator from "./LoadingIndicator";
import "../../static/css/Auth/LoginForm.css";

const lowLetter = "abcdefghijklmnopqrstuvwxyz";
const highLetter = lowLetter.toUpperCase();
const symbols = "!@#$%^&*()_+-=[]{}|;:',.<>?/";

// Définition du type des props
interface FormProps {
  route: string;
  method: "login" | "register";
}

function isPasswordValid(password: string) {
  const hasLowerCase = [...password].some((char) => lowLetter.includes(char));
  const hasUpperCase = [...password].some((char) => highLetter.includes(char));
  const hasSymbol = [...password].some((char) => symbols.includes(char));
  const hasDigit = /\d/.test(password);

  return (
    hasLowerCase &&
    hasUpperCase &&
    hasSymbol &&
    hasDigit &&
    password.length >= 8
  );
}

const isEmailValid = (email: string): boolean => {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email);
};

const LoginForm: React.FC<FormProps> = ({ route, method }) => {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [passwordCriteria, setPasswordCriteria] = useState({
    hasLowerCase: false,
    hasUpperCase: false,
    hasDigit: false,
    hasSymbol: false,
    isLongEnough: false,
  });

  const navigate = useNavigate();
  const name = method === "login" ? "Login" : "Register";

  const updatePasswordCriteria = (pwd: string) => {
    setPasswordCriteria({
      hasLowerCase: [...pwd].some((char) => lowLetter.includes(char)),
      hasUpperCase: [...pwd].some((char) => highLetter.includes(char)),
      hasDigit: /\d/.test(pwd),
      hasSymbol: [...pwd].some((char) => symbols.includes(char)),
      isLongEnough: pwd.length >= 8,
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    // // if (method === "register") {
    // //   if (!isEmailValid(email)) {
    // //     alert("Veuillez entrer une adresse email valide.");
    // //     setLoading(false);
    // //     return;
    // //   }

    // //   if (!isPasswordValid(password)) {
    // //     alert(
    // //       "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un symbole."
    // //     );
    // //     setLoading(false);
    // //     return;
    // //   }
    // // }

    try {
      const res = await api.post(route, { email, password });
      if (method === "login") {
        localStorage.setItem(ACCESS_TOKEN, res.data.access);
        localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
        navigate("/portfolio/dashboard");
      } else {
        navigate("/login");
      }
    } catch (error) {
      alert(error);
    } finally {
      setLoading(false);
    }
  };

  const PasswordRequirement = ({
    valid,
    label,
  }: {
    valid: boolean;
    label: string;
  }) => (
    <div className="password-requirement">
      <span style={{ color: valid ? "green" : "red" }}>
        {valid ? "✔️" : "❌"} {label}
      </span>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="login-form-container">
      <h1 className="title-form">{name}</h1>

      <input
        className="login-form-input"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />

      <input
        className="login-form-input"
        type="password"
        value={password}
        onChange={(e) => {
          const value = e.target.value;
          setPassword(value);
          updatePasswordCriteria(value);
        }}
        placeholder="Password"
        required
      />

      {method === "register" && (
        <div className="password-validation">
          <PasswordRequirement
            valid={passwordCriteria.hasLowerCase}
            label="Une lettre minuscule"
          />
          <PasswordRequirement
            valid={passwordCriteria.hasUpperCase}
            label="Une lettre majuscule"
          />
          <PasswordRequirement
            valid={passwordCriteria.hasDigit}
            label="Un chiffre"
          />
          <PasswordRequirement
            valid={passwordCriteria.hasSymbol}
            label="Un symbole"
          />
          <PasswordRequirement
            valid={passwordCriteria.isLongEnough}
            label="Au moins 8 caractères"
          />
        </div>
      )}

      {loading && <LoadingIndicator />}

      <button className="login-form-button" type="submit">
        {name}
      </button>
    </form>
  );
};

export default LoginForm;
