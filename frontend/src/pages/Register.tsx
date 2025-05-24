import Form from "../components/Auth/LoginForm";

function Register() {
  return <Form route="/api/user/register/" method="register" />;
}

export default Register;
