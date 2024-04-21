import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import styles from "./Navbar.module.css";
import ListTimeFrame from "./ListTimeFrame";
import { NavLink } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faCaretDown } from "@fortawesome/free-solid-svg-icons";

const Navbar = (props) => {
  const [showTimeFrames, setShowTimeFrames] = useState(false);
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
          <button className={styles.toggleTimeFramesBtn} onClick={handleClick}>
            <FontAwesomeIcon
              icon={faCaretDown}
              className={
                showTimeFrames
                  ? styles.showTimeFramesIcon
                  : styles.hideTimeFramesIcon
              }
            />
          </button>
        )}
        <div
          className={
            showTimeFrames ? styles.showTimeFrames : styles.hideTimeFrames
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
                />
              );
            })}
        </div>
      </div>
      <div className={styles.menu}>
        <NavLink
          className={(navData) =>
            navData.isActive ? `${styles.pages} ${styles.active}` : styles.pages
          }
          to="/chart"
        >
          Chart
        </NavLink>
        <NavLink
          className={(navData) =>
            navData.isActive ? `${styles.pages} ${styles.active}` : styles.pages
          }
          to="/strategies"
        >
          Strategies
        </NavLink>
        <NavLink
          className={(navData) =>
            navData.isActive ? `${styles.pages} ${styles.active}` : styles.pages
          }
          to="/review"
        >
          Review
        </NavLink>
        <div className={styles.account}>
          <FontAwesomeIcon icon={faUser} />
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
