import React, { useState, useEffect, useContext } from "react";
import styles from "./AccountSummary.module.css";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";

const AccountSummary = () => {
  const fetchData = useFetch();
  const [summary, setSummary] = useState();
  const appCtx = useContext(AppContext);

  const getSummary = async () => {
    const res = await fetchData(
      "/api/tradesMenu/summary/",
      "GET",
      undefined,
      appCtx.accessToken
    );

    if (res.ok) {
      setSummary(res.data.summary);
    }
  };

  useEffect(() => {
    getSummary();
  }, []);

  return (
    <div className={`container-fluid ${styles.container}`}>
      <div className={`row ${styles.subheader}`}>
        <div className="col">Currency</div>
        <div className="col">NAV</div>
        <div className="col">Balance</div>
        <div className="col">Unrealized P/L</div>
        <div className="col">Realized P/L</div>
        <div className="col">Margin Used</div>
        <div className="col">Margin Available</div>
        <div className="col">Leverage</div>
      </div>
      {summary && (
        <div className={`row ${styles.rows}`}>
          <div className="col">{summary.currency}</div>
          <div className="col">{Number(summary.nav).toFixed(2)}</div>
          <div className="col">{Number(summary.balance).toFixed(2)}</div>
          <div
            className={`col ${
              summary.unrealized_pl >= 0 ? styles.upColour : styles.downColour
            }`}
          >
            {Number(summary.unrealized_pl).toFixed(2)}
          </div>
          <div
            className={`col ${
              summary.realized_pl >= 0 ? styles.upColour : styles.downColour
            }`}
          >
            {Number(summary.realized_pl).toFixed(2)}
          </div>
          <div className="col">{Number(summary.margin_used).toFixed(2)}</div>
          <div className="col">
            {Number(summary.margin_available).toFixed(2)}
          </div>
          <div className="col">{summary.leverage}</div>
        </div>
      )}
    </div>
  );
};

export default AccountSummary;
