import React from "react";
import styles from "./styles/HomePage.module.css";

const HomePage = () => {
  return (
    <div className={styles.main}>
      <img src={`./src/assets/Logo.png`} className={styles.logo} />
      <h1 className={styles.title}>Trader Joe</h1>
    </div>
  );
};

export default HomePage;
