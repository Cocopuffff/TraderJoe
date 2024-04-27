import React from "react";
import styles from "./TradesMenu.module.css";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import MinimizeIcon from "@mui/icons-material/Minimize";

const TradesNavbar = (props) => {
  const handleClick = (event) => {
    props.setViewTrades(true);
    props.setActive(event.target.id);
  };

  return (
    <div
      className={
        props.viewTrades
          ? `${styles["tab-active"]}`
          : `${styles["tab-inactive"]}`
      }
    >
      <div className={styles.tabnav}>
        <button
          onClick={handleClick}
          id="positions"
          className={
            props.active === "positions"
              ? `${styles.activeSubheader}`
              : `${styles.subheader}`
          }
        >
          Positions
        </button>
        <button
          onClick={handleClick}
          id="summary"
          className={
            props.active === "summary"
              ? `${styles.activeSubheader}`
              : `${styles.subheader}`
          }
        >
          Account Summary
        </button>
        <button
          onClick={handleClick}
          id="history"
          className={
            props.active === "history"
              ? `${styles.activeSubheader}`
              : `${styles.subheader}`
          }
        >
          History
        </button>
        <button
          onClick={handleClick}
          id="strategies"
          className={
            props.active === "strategies"
              ? `${styles.activeSubheader}`
              : `${styles.subheader}`
          }
        >
          Run Strategies
        </button>
      </div>
      {props.viewTrades ? (
        <div
          onClick={() => props.setViewTrades(false)}
          className={styles.toggle}
        >
          <MinimizeIcon />
        </div>
      ) : (
        <div
          onClick={() => props.setViewTrades(true)}
          className={styles.toggle}
        >
          <FullscreenIcon />
        </div>
      )}
    </div>
  );
};

export default TradesNavbar;
