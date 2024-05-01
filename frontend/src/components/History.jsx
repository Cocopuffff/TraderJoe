import React, { useState, useEffect, useContext } from "react";
import styles from "./History.module.css";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";

const History = () => {
  const fetchData = useFetch();
  const [closedTrades, setClosedTrades] = useState();
  const appCtx = useContext(AppContext);

  const getClosedTrades = async () => {
    const res = await fetchData(
      "/api/tradesMenu/history/",
      "GET",
      undefined,
      appCtx.accessToken
    );

    if (res.ok) {
      setClosedTrades(res.data.history);
    }
  };

  useEffect(() => {
    getClosedTrades();
  }, []);

  return (
    <div className={`container-fluid ${styles.container}`}>
      <div className={`row ${styles.subheader}`}>
        <div className="col">Date / Time</div>
        <div className="col">Symbol</div>
        <div className="col">Units</div>
        <div className="col">Side</div>
        <div className="col">Price</div>
        <div className="col">Profit</div>
        <div className="col">Financing</div>
        <div className="col">Transaction ID</div>
      </div>
      {closedTrades &&
        closedTrades.map((trade) => {
          return (
            <div className={`row ${styles.rows}`} key={trade.id}>
              <div className="col">
                {new Intl.DateTimeFormat("en-GB", {
                  dateStyle: "short",
                  timeStyle: "short",
                }).format(new Date(trade.close_time))}
              </div>
              <div className="col">{trade.instrument}</div>
              <div className="col">
                {Number(trade.initial_units).toFixed(0)}
              </div>
              <div className="col">
                {trade.initial_units > 0 ? "Long" : "Short"}
              </div>
              <div className="col">{trade.price}</div>
              <div
                className={`col ${
                  trade.realized_pl >= 0 ? styles.upColour : styles.downColour
                }`}
              >
                {Number(trade.realized_pl).toFixed(2)}
              </div>
              <div
                className={`col ${
                  trade.financing >= 0 ? styles.upColour : styles.downColour
                }`}
              >
                {Number(trade.financing).toFixed(2)}
              </div>
              <div className="col">{trade.transaction_id}</div>
            </div>
          );
        })}
    </div>
  );
};

export default History;
