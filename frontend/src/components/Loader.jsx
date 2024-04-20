import React from "react";
import styles from "./Loader.module.css";

const Loader = () => {
  return (
    <div className={styles.sea}>
      <div className={styles["circle-wrapper"]}>
        <div className={styles.bubble}></div>
        <div className={styles["submarine-wrapper"]}>
          <div className={styles["submarine-body"]}>
            <div className={styles.window}></div>
            <div className={styles.engine}></div>
            <div className={styles.light}></div>
          </div>
          <div className={styles.helix}></div>
          <div className={styles.hat}>
            <div className={styles["leds-wrapper"]}>
              <div className={styles.periscope}></div>
              <div className={styles.leds}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Loader;
