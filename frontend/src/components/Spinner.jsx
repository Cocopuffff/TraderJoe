import React from "react";
import styles from "./Spinner.module.css";

const Spinner = () => {
  return (
    <div className={styles.center}>
      <div className={styles["lds-dual-ring"]}></div>
    </div>
  );
};

export default Spinner;
