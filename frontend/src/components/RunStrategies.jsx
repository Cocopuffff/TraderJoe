import React, { useState, useEffect, useContext } from "react";
import styles from "./RunStrategies.module.css";
import useFetch from "../hooks/useFetch";
import ClearIcon from "@mui/icons-material/Clear";
import AppContext from "../context/AppContext";

const RunStrategies = () => {
  const fetchData = useFetch();
  const [stratInstTradeList, setStratInstTradeList] = useState([]);
  const [strategyDropdownList, setStrategyDropdownList] = useState([]);
  const [instruments, setInstruments] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [selectedInstrument, setSelectedInstrument] = useState("");

  const appCtx = useContext(AppContext);

  const handleChange = (event) => {
    switch (event.currentTarget.id) {
      case "strategy":
        setSelectedStrategy(event.target.value);
        break;
      case "instrument":
        setSelectedInstrument(event.target.value);
        break;
      default:
        console.log(event.target.value);
    }
  };

  const handleDelete = async (event) => {
    try {
      const res = await fetchData(
        "/api/strategy/stop/",
        "DELETE",
        { active_id: event.currentTarget.id },
        appCtx.accessToken
      );

      if (res.ok) {
        getList();
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  const handleStart = async () => {
    console.log(`selectedStrategy: ${selectedStrategy}`);
    console.log(`selectedInstrument: ${selectedInstrument}`);
    try {
      const body = {
        instrument: selectedInstrument,
        strategy_id: selectedStrategy,
      };

      const res = await fetch(
        import.meta.env.VITE_SERVER + "/api/strategy/start/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + appCtx.accessToken,
          },
          body: JSON.stringify(body),
        }
      );

      if (res.ok) {
        const data = await res.json();
        console.log(data);
        getList();
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  const getList = async () => {
    try {
      const res = await fetchData(
        "/api/tradesMenu/strategies/",
        "GET",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        setStratInstTradeList(res.data.strategy_instrument_trade);
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  const getStrategyDropdownList = async () => {
    try {
      const res = await fetchData(
        "/api/strategy/",
        "GET",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        setStrategyDropdownList(res.data.strategies);
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data.msg);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  const getValidInstruments = async () => {
    try {
      const res = await fetchData(
        "/api/watchlist/all/",
        "GET",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        setInstruments(
          res.data.instruments.toSorted((a, b) => {
            const nameA = a.display_name.toUpperCase();
            const nameB = b.display_name.toUpperCase();
            if (nameA > nameB) {
              return 1;
            } else if (nameA < nameB) {
              return -1;
            } else {
              return 0;
            }
          })
        );
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data.msg);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  useEffect(() => {
    getList();
    getStrategyDropdownList();
    getValidInstruments();
  }, []);

  return (
    <div className={`container-fluid ${styles.container}`}>
      <div className={`row ${styles.subheader}`}>
        <div className="col">Strategy Name</div>
        <div className="col">Instrument</div>
        <div className="col">Side</div>
        <div className="col">Status</div>
        <div className="col">Actions</div>
      </div>
      {stratInstTradeList &&
        stratInstTradeList.map((item) => {
          return (
            <div className={`row ${styles.rows}`} key={item.id}>
              <div className="col">{item.strategy_name}</div>
              <div className="col">{item.instrument}</div>
              <div
                className={`col ${
                  Number(item.initial_units) > 0
                    ? styles.longColour
                    : styles.downColour
                }`}
              >
                {item.initial_units == null
                  ? ""
                  : Number(item.initial_units) > 0
                  ? "Long"
                  : "Short"}
              </div>
              <div className="col">
                {item.pid && !item.trade_id && "Pending signal"}
                {!item.is_active && Number(item.units) != 0 && "Open Trade"}
                {!item.is_active && item.units === null && "Inactive"}
                {!item.is_active && item.units === "0.000" && "Closed"}
              </div>
              <div className="col">
                <button
                  id={item.id}
                  onClick={handleDelete}
                  className={styles.deleteButton}
                >
                  <ClearIcon />
                </button>
              </div>
            </div>
          );
        })}
      <div className={`row ${styles.rows}`}>
        <div className="col">
          <div className={`row ${styles.inputWrapper}`}>
            <select
              name="strategy"
              id="strategy"
              value={selectedStrategy}
              className={styles.input}
              onChange={handleChange}
            >
              <option value="" disabled>
                Select a strategy
              </option>
              {strategyDropdownList &&
                strategyDropdownList.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.name}
                  </option>
                ))}
            </select>
          </div>
        </div>
        <div className="col">
          <div className={`row ${styles.inputWrapper}`}>
            <select
              name="instrument"
              id="instrument"
              value={selectedInstrument}
              className={styles.input}
              onChange={handleChange}
            >
              <option value="" disabled>
                Select an instrument
              </option>
              {instruments &&
                instruments.map((item) => (
                  <option value={item.name} key={item.name}>
                    {item.display_name}
                  </option>
                ))}
            </select>
          </div>
        </div>
        <div className="col">
          <div className={`row ${styles.inputWrapper}`}>
            <button onClick={handleStart} className={styles.buttonGood}>
              Run Strategy
            </button>
          </div>
        </div>
        <div className="col"></div>
        <div className="col"></div>
      </div>
      {JSON.stringify(stratInstTradeList)}
    </div>
  );
};

export default RunStrategies;
