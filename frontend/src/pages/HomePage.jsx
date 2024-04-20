import React from "react";
import styles from "./styles/HomePage.module.css";

const HomePage = () => {
  return (
    <div className={styles.main}>
      <img src={`./src/assets/LogoFull.png`} className={styles.logo} />
      <div className={styles.animationHolder}>
        <div className={styles["logo-holder"]}>
          <div className={styles.bar}></div>
          <div className={`${styles.bar} ${styles.fill1}`}></div>
          <div className={`${styles.bar} ${styles.fill2}`}></div>
          <div className={`${styles.bar} ${styles.fill3}`}></div>
          <div className={`${styles.bar} ${styles.fill4}`}></div>
          <div className={`${styles.bar} ${styles.fill1}`}></div>
          <div className={`${styles.bar} ${styles.fill5}`}></div>
          <div className={`${styles.bar} ${styles.fill6}`}></div>
          <div className={styles.bar}></div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
