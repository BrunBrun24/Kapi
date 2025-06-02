"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "@/constants";
import api from "@/api";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "module";

const lowLetter = "abcdefghijklmnopqrstuvwxyz";
const highLetter = lowLetter.toUpperCase();
const symbols = "!@#$%^&*()_+-=[]{}|;:',.<>?/";

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

interface LoginFormProps extends React.ComponentProps<"div"> {
  method: "login" | "register";
}

export function LoginRegisterForm({
  method,
  className,
  ...props
}: LoginFormProps) {
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

  const navigate = useRouter();
  const name = method === "login" ? "Se connecter" : "S'enregistrer";
  const road = method === "login" ? "/api/token/" : "/api/user/register/";

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
      const res = await api.post(road, { email, password });
      if (method === "login") {
        // 1. LocalStorage
        localStorage.setItem(ACCESS_TOKEN, res.data.access);
        localStorage.setItem(REFRESH_TOKEN, res.data.refresh);

        // 2. Cookie visible du serveur
        document.cookie = `access_token=${res.data.access}; path=/; secure; SameSite=Lax`;
        document.cookie = `refresh_token=${res.data.refresh}; path=/; secure; SameSite=Lax`;

        // 3. Redirection
        navigate.push("/portfolio/dashboard");
      } else {
        navigate.push("/login");
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
  }) => {
    return (
      <li className="flex items-center gap-2 text-sm text-muted-foreground">
        <span
          className={
            valid
              ? "text-green-600 dark:text-green-400"
              : "text-red-600 dark:text-red-400"
          }
        >
          {valid ? "✅" : "❌"}
        </span>
        {label}
      </li>
    );
  };

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">
            {method === "login" ? (
              <p>Bon retour parmis nous !</p>
            ) : (
              <p>Bienvenue</p>
            )}
          </CardTitle>
          {/* <CardDescription>
            Connectez-vous avec votre compte Apple ou Google
          </CardDescription> */}
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-6">
              {/* <div className="flex flex-col gap-4">
                <Button variant="outline" className="w-full">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path
                      d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"
                      fill="currentColor"
                    />
                  </svg>
                  Login with Apple
                </Button>
                <Button variant="outline" className="w-full">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path
                      d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                      fill="currentColor"
                    />
                  </svg>
                  Login with Google
                </Button>
              </div>
              <div className="after:border-border relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
                <span className="bg-card text-muted-foreground relative z-10 px-2">
                  Or continue with
                </span>
              </div> */}
              <div className="grid gap-6">
                <div className="grid gap-3">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="grid gap-3">
                  <div className="flex items-center">
                    <Label htmlFor="password">Mot de passe</Label>
                    {method === "login" && (
                      <Link
                        href="#"
                        className="ml-auto text-sm underline-offset-4 hover:underline"
                      >
                        Mot de passe oublié ?
                      </Link>
                    )}
                  </div>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => {
                      const value = e.target.value;
                      setPassword(value);
                      updatePasswordCriteria(value);
                    }}
                  />

                  {method === "register" && (
                    <div className="rounded-lg border border-muted p-4 bg-muted/30">
                      <p className="text-sm font-medium text-muted-foreground mb-2">
                        Le mot de passe doit contenir :
                      </p>
                      <ul className="space-y-1">
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
                      </ul>
                    </div>
                  )}
                </div>
                <Button type="submit" className="w-full">
                  {method === "login" ? "Se connecter" : "S'inscrire"}
                </Button>
              </div>
              {method === "login" ? (
                <div className="text-center text-sm">
                  Vous n'avez pas de compte ?{" "}
                  <Link
                    href="/sign-up"
                    className="underline underline-offset-4"
                  >
                    Créer un compte
                  </Link>
                </div>
              ) : (
                <div className="text-center text-sm">
                  Vous avez un compte ?{" "}
                  <Link href="/login" className="underline underline-offset-4">
                    Se connecter
                  </Link>
                </div>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
      <div className="text-muted-foreground text-center text-xs text-balance">
        En cliquant sur continuer, vous acceptez nos{" "}
        <Link
          href="#"
          className="underline underline-offset-4 hover:text-primary"
        >
          conditions d’utilisation
        </Link>{" "}
        et{" "}
        <Link
          href="#"
          className="underline underline-offset-4 hover:text-primary"
        >
          politique de confidentialité
        </Link>
        .
      </div>
    </div>
  );
}
