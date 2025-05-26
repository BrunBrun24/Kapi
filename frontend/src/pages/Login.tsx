import LoginForm from "../components/auth/LoginForm";

function Login() {
  return <LoginForm route="/api/token/" method="login" />;
}

export default Login;
