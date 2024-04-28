import React, { useState, useEffect, useContext } from "react";
import styles from "./styles/ReviewTraders.module.css";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";

const ReviewTraders = () => {
  const fetchData = useFetch();
  const [performanceData, setPerformanceData] = useState([]);
  const appCtx = useContext(AppContext);

  const getPerformanceData = async () => {
    try {
      const res = await fetchData(
        "/api/review/performance/",
        "GET",
        undefined,
        appCtx.accessToken
      );
      if (res.ok) {
        setPerformanceData(res.data.performances);
      }
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    getPerformanceData();
  }, []);

  return (
    <div className="container">
      Review your traders here!
      <div>{JSON.stringify(performanceData)}</div>
      <div className={`row ${styles.tableheader}`}>
        <div className="col-md-2">Trader</div>
        <div className="col-md-1">Initial Balance</div>
        <div className="col-md-1">Current NAV</div>
        <div className="col-md-6">
          <div className="row">
            <div className="col">Performance yesterday</div>
            <div className="col">Performance last 7 days</div>
            <div className="col">Performance last 30 days</div>
            <div className="col">Performance this year</div>
          </div>
        </div>

        <div className="col-md-2">Actions</div>
      </div>
      {performanceData &&
        performanceData.map((item) => {
          return (
            <div className="row" key={item.id}>
              <div className="col-md-2">
                <div>{item.email}</div>
                <div>{item.display_name}</div>
              </div>
              <div className="col-md-1">
                {Number(item.initial_balance).toFixed(2)}
              </div>
              <div
                className={`col-md-1 ${
                  item.current_nav >= item.initial_balance
                    ? styles.upColour
                    : styles.downColour
                }`}
              >
                {Number(item.current_nav).toFixed(2)}
              </div>
              <div className="col-md-6">
                <div className="row">
                  <div className="col">
                    <div
                      className={
                        item.yesterday_net_realized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.yesterday_net_realized_pl).toFixed(2)}
                    </div>
                    <div
                      className={
                        item.yesterday_unrealized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.yesterday_unrealized_pl).toFixed(2)}
                    </div>
                  </div>
                  <div className="col">
                    <div
                      className={
                        item.last_7_days_net_realized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.last_7_days_net_realized_pl).toFixed(2)}
                    </div>
                    <div
                      className={
                        item.last_7_days_unrealized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.last_7_days_unrealized_pl).toFixed(2)}
                    </div>
                  </div>
                  <div className="col">
                    <div
                      className={
                        item.last_30_days_net_realized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.last_30_days_net_realized_pl).toFixed(2)}
                    </div>
                    <div
                      className={
                        item.last_30_days_unrealized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.last_30_days_unrealized_pl).toFixed(2)}
                    </div>
                  </div>
                  <div className="col">
                    <div
                      className={
                        item.ytd_net_realized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.ytd_net_realized_pl).toFixed(2)}
                    </div>
                    <div
                      className={
                        item.ytd_unrealized_pl >= 0
                          ? styles.upColour
                          : styles.downColour
                      }
                    >
                      {Number(item.ytd_unrealized_pl).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="col-md-2">Actions</div>
            </div>
          );
        })}
    </div>
  );
};

export default ReviewTraders;
