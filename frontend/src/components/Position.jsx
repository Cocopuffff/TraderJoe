import React, { useState, useEffect, useContext } from "react";
import styles from "./Position.module.css";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";

const Position = () => {
  const fetchData = useFetch();
  const [positions, setPositions] = useState();
  const appCtx = useContext(AppContext);

  const getPositions = async () => {
    const res = await fetchData(
      "/api/tradesMenu/positions/",
      "GET",
      undefined,
      appCtx.accessToken
    );

    if (res.ok) {
      setPositions(res.data.positions);
    }
  };

  useEffect(() => {
    getPositions();
  }, []);

  return (
    <div className={`container-fluid ${styles.container}`}>
      <div className={`row ${styles.subheader}`}>
        <div className="col">Strategy Name</div>
        <div className="col">Instrument</div>
        <div className="col">Units</div>
        <div className="col">Side</div>
        <div className="col">Profit</div>
        <div className="col">Transaction ID</div>
      </div>
      {positions &&
        positions.map((trade) => {
          return (
            <div className={`row ${styles.rows}`} key={trade.id}>
              <div className="col">{trade.strategy_name}</div>
              <div className="col">{trade.instrument}</div>
              <div className="col">{Number(trade.units).toFixed(0)}</div>
              <div
                className={`col ${
                  trade.units > 0 ? styles.longColour : styles.downColour
                }`}
              >
                {trade.units > 0 ? "Long" : "Short"}
              </div>
              <div
                className={`col ${
                  trade.unrealized_pl >= 0 ? styles.upColour : styles.downColour
                }`}
              >
                {Number(trade.unrealized_pl).toFixed(2)}
              </div>
              <div className="col">{trade.id}</div>
            </div>
          );
        })}
    </div>
  );
};

export default Position;
