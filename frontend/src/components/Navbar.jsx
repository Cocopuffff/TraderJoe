import React, { useState, useContext } from "react";
import { useLocation } from "react-router-dom";
import styles from "./Navbar.module.css";
import ListTimeFrame from "./ListTimeFrame";
import { NavLink } from "react-router-dom";
import AccountCircleRoundedIcon from "@mui/icons-material/AccountCircleRounded";
import ArrowDropDownRoundedIcon from "@mui/icons-material/ArrowDropDownRounded";
import AppContext from "../context/AppContext";

const Navbar = (props) => {
  const appCtx = useContext(AppContext);
  const [showTimeFrames, setShowTimeFrames] = useState(false);
  const [viewAccountActions, setViewAccountActions] = useState(false);
  const location = useLocation();
  const isChart = location.pathname === "/chart";
  const handleClick = () => {
    setShowTimeFrames(!showTimeFrames);
  };

  return (
    <nav className={styles.navbar}>
      <div className={styles.submenu}>
        <NavLink to="/" className={styles.logoContainer}>
          <img src="../src/assets/Logo.png" className={styles.logo} />
        </NavLink>

        {isChart && (
          <div className={styles.timeFrame}>
            <div className={`${styles.active}`}>
              {props.selectedTimeFrame.displayShort}
            </div>
            <button
              className={styles.toggleTimeFramesBtn}
              onClick={handleClick}
            >
              <ArrowDropDownRoundedIcon
                className={
                  showTimeFrames
                    ? styles.showTimeFramesIcon
                    : styles.hideTimeFramesIcon
                }
              />
            </button>
            <div
              className={
                showTimeFrames ? styles.dropdown : styles.hideTimeFrames
              }
            >
              {isChart &&
                props.timeFrames.map((timeFrame, idx) => {
                  return (
                    <ListTimeFrame
                      timeFrame={timeFrame}
                      key={idx}
                      setSelectedTimeFrame={props.setSelectedTimeFrame}
                      selectedTimeFrame={props.selectedTimeFrame}
                      setShowTimeFrames={setShowTimeFrames}
                    />
                  );
                })}
            </div>
          </div>
        )}
      </div>
      <div>id: {appCtx.id}</div>
      <div>role: {appCtx.role}</div>
      <div>access exp: {appCtx.expirationDate.toLocaleString()}</div>
      <div className={styles.menu}>
        {appCtx.role === "Trader" && (
          <>
            <NavLink
              className={(navData) =>
                navData.isActive
                  ? `${styles.pages} ${styles.active}`
                  : styles.pages
              }
              to="/chart"
            >
              Chart
            </NavLink>
            <NavLink
              className={(navData) =>
                navData.isActive
                  ? `${styles.pages} ${styles.active}`
                  : styles.pages
              }
              to="/strategies"
            >
              Strategies
            </NavLink>
          </>
        )}
        {appCtx.role === "Manager" && (
          <NavLink
            className={(navData) =>
              navData.isActive
                ? `${styles.pages} ${styles.active}`
                : styles.pages
            }
            to="/review"
          >
            Review
          </NavLink>
        )}

        <div
          className={styles.account}
          onClick={() => setViewAccountActions(!viewAccountActions)}
        >
          <AccountCircleRoundedIcon />
          {viewAccountActions && (
            <div className={styles.dropdown}>
              {!appCtx.accessToken && (
                <>
                  <NavLink
                    className={(navData) =>
                      navData.isActive
                        ? `${styles.pages} ${styles.active}`
                        : styles.pages
                    }
                    to="/login"
                  >
                    Login
                  </NavLink>
                  <NavLink
                    className={(navData) =>
                      navData.isActive
                        ? `${styles.pages} ${styles.active}`
                        : styles.pages
                    }
                    to="/register"
                  >
                    Register
                  </NavLink>
                </>
              )}
              {appCtx.accessToken && (
                <NavLink to="/" onClick={appCtx.logOut}>
                  Logout
                </NavLink>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
