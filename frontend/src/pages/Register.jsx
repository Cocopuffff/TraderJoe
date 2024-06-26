import React, { useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";
import styles from "./styles/Register.module.css";
import Logo from "../assets/Logo.png";

const Register = () => {
  const fetchData = useFetch();
  const appCtx = useContext(AppContext);
  const navigate = useNavigate();

  const [roles, setRoles] = useState([]);
  const [duplicateDisplayNameWarning, setDuplicateDisplayNameWarning] =
    useState(false);
  const [duplicateEmailWarning, setDuplicateEmailWarning] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accountType, setAccountType] = useState("");
  const [secretKey, setSecretKey] = useState("");

  function emailIsValid(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  const handleChange = (event) => {
    switch (event.currentTarget.id) {
      case "displayName":
        setDisplayName(event.currentTarget.value);
        checkDuplicateName(displayName);
        break;
      case "email":
        const emailInput = event.currentTarget.value;
        setEmail(emailInput);
        emailIsValid(emailInput) ? checkDuplicateEmail(emailInput) : "";
        break;
      case "password":
        setPassword(event.currentTarget.value);
        break;
      case "user-type":
        setAccountType(event.currentTarget.value);
        break;
      case "secret-key":
        setSecretKey(event.currentTarget.value);
        break;
      default:
        appCtx.setErrorMessage(
          `something went wrong! id: ${event.currentTarget.id}, value: ${event.currentTarget.value}`
        );
        appCtx.isError(true);
        break;
    }
  };

  const getRoles = async () => {
    const res = await fetchData("/auth/roles/");
    if (res.ok) {
      setRoles(res.data.account_types);
    } else {
      appCtx.setErrorMessage(res.data);
      appCtx.isError(true);
    }
  };

  const checkDuplicateName = async (name_input) => {
    try {
      const res = await fetchData(
        "/auth/check-name/",
        "POST",
        { display_name: name_input },
        undefined
      );

      if (res.data === "duplicate name") {
        setDuplicateDisplayNameWarning(true);
        return;
      }

      if (res.ok) {
        setDuplicateDisplayNameWarning(false);
      }
    } catch (error) {
      appCtx.setErrorMessage(res.data);
      appCtx.isError(true);
    }
  };

  const checkDuplicateEmail = async (emailInput) => {
    try {
      const res = await fetchData(
        "/auth/check-email/",
        "POST",
        { email: emailInput },
        undefined
      );

      if (res.data === "duplicate email") {
        setDuplicateEmailWarning(true);
        return;
      }

      if (res.ok) {
        setDuplicateEmailWarning(false);
      }
    } catch (error) {
      appCtx.setErrorMessage(res.data);
      appCtx.isError(true);
    }
  };

  const registerUser = async (event) => {
    try {
      event.preventDefault();
      if (!(displayName && email && password && roles)) {
        throw new Error("Mandatory fields have to be filled.");
      }

      const newUser = {
        display_name: displayName,
        email: email,
        password: password,
        role: accountType,
      };

      if (accountType === "Manager") {
        if (!secretKey) {
          throw new Error("Mandatory fields have to be filled.");
        }
        newUser.secret_key = secretKey;
      }
      const res = await fetchData("/auth/register/", "PUT", newUser, undefined);
      if (res.ok) {
        setEmail("");
        setPassword("");
        setAccountType("");
        setSecretKey("");
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
    getRoles();
  }, []);

  //   useEffect(() => {}, [accountType, duplicateEmailWarning]);

  return (
    <>
      <div className="container-fluid d-flex flex-column justify-content-center">
        <div className={styles.header}>
          <img className={styles.logo} src={Logo} alt="Trader Joe" />
          <h2 className={styles.title}>Register for an account</h2>
        </div>
        <form className={styles.form}>
          <div className="input-group mb-3">
            <label
              htmlFor="displayName"
              className="input-group-text bg-dark-subtle"
            >
              Name<span className="required">*</span>
            </label>
            <input
              id="displayName"
              name="displayName"
              type="text"
              placeholder="Trader Joe"
              onChange={handleChange}
              value={displayName}
              className="form-control"
              required
            />
          </div>
          {duplicateDisplayNameWarning && (
            <div className="required warning">
              <em>Display name is already registered.</em>
            </div>
          )}
          <div className="input-group mb-3">
            <label htmlFor="email" className="input-group-text bg-dark-subtle">
              Email<span className="required">*</span>
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="example@email.com"
              onChange={handleChange}
              value={email}
              className="form-control"
              required
            />
          </div>
          {duplicateEmailWarning && (
            <div className="required warning">
              <em>Email is already registered.</em>
            </div>
          )}
          <div className="input-group mb-3">
            <label
              htmlFor="password"
              className="input-group-text bg-dark-subtle"
            >
              Password<span className="required">*</span>
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="********"
              onChange={handleChange}
              value={password}
              className="form-control"
              required
            />
          </div>
          <div className="input-group mb-3">
            <label
              htmlFor="user-type"
              className="input-group-text bg-dark-subtle"
            >
              User Type<span className="required">*</span>
            </label>
            <select
              id="user-type"
              name="user-type"
              onChange={handleChange}
              value={accountType}
              className="form-select"
              required
            >
              <option value="" disabled>
                Select an account type
              </option>
              {roles &&
                roles.map((role) => {
                  return (
                    <option value={role} key={role}>
                      {role}
                    </option>
                  );
                })}
            </select>
          </div>
          {accountType === "Manager" && (
            <>
              <div className="input-group mb-3">
                <label
                  htmlFor="secretKey"
                  className="input-group-text bg-dark-subtle"
                >
                  Secret Key<span className="required">*</span>
                </label>
                <input
                  id="secret-key"
                  name="secret-key"
                  type="password"
                  placeholder="********"
                  onChange={handleChange}
                  value={secretKey}
                  className="form-control"
                  required
                />
              </div>
            </>
          )}
          <div>
            <button
              type="submit"
              className={`btn ${styles.button}`}
              onClick={registerUser}
            >
              Register
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default Register;
