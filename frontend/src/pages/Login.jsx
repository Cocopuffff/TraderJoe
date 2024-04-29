import React, { useState, useContext, useEffect } from "react";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";
import { jwtDecode } from "jwt-decode";
import { useNavigate } from "react-router-dom";
import styles from "./styles/Login.module.css";
import Logo from "../assets/Logo.png";

const Login = () => {
  const fetchData = useFetch();
  const appCtx = useContext(AppContext);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (event) => {
    try {
      event.preventDefault();
      const res = await fetchData(
        "/auth/login/",
        "POST",
        { email: email, password: password },
        undefined
      );

      if (res.ok) {
        appCtx.setAccessToken(res.data.access);
        const decoded = jwtDecode(res.data.access);
        const expirationDate = new Date(decoded.exp * 1000);
        appCtx.setExpirationDate(expirationDate);
        appCtx.setId(decoded.id);
        appCtx.setRole(decoded.role);
        appCtx.setDisplayName(decoded.name);
        appCtx.setEmail(email);
        localStorage.setItem("refreshToken", res.data.refresh);
        setEmail("");
        setPassword("");
        navigate("/");
      } else {
        throw new Error(res.data);
      }
    } catch (error) {
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  useEffect(() => {
    appCtx.setShowLogin(false);
  }, []);

  return (
    <>
      <div className="container-fluid d-flex flex-column justify-content-center">
        <div className={styles.header}>
          <img className={styles.logo} src={Logo} alt="Trader Joe" />
          <h2 className={styles.title}>Log in to your account</h2>
        </div>

        <form className={styles.form}>
          <div className="input-group mb-3">
            <label htmlFor="email" className="input-group-text bg-dark-subtle">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="example@email.com"
              onChange={(event) => setEmail(event.target.value)}
              value={email}
              className="form-control"
              required
            />
          </div>
          <div className="input-group mb-3">
            <label
              htmlFor="password"
              className="input-group-text bg-dark-subtle"
            >
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="********"
              onChange={(event) => setPassword(event.target.value)}
              value={password}
              className="form-control"
              required
            />
          </div>
          <div className="">
            <a href="#" className={styles.links}>
              Forgot password?
            </a>
          </div>
          <div>
            <button
              type="submit"
              className={`btn ${styles.button}`}
              onClick={handleLogin}
            >
              Log in
            </button>
          </div>
        </form>

        <p className="text-center">
          Not a member?
          <a href="/register" className={styles.links}>
            Create an account now!
          </a>
        </p>
      </div>
    </>
  );
};

export default Login;
