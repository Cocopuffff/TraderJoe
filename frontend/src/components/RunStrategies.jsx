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
    switch (event.target.id) {
      case "strategy":
        setSelectedStrategy(event.target.value);
      case "instrument":
        setSelectedInstrument(event.target.value);
      default:
        console.log(event.target.id);
    }
  };

  const handleDelete = async (event) => {
    try {
      const res = await fetchData(
        "/api/tradesMenu/strategies/",
        "DELETE",
        { id: event.currentTarget.id },
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

  const handleStart = () => {
    console.log(`selectedStrategy: ${selectedStrategy}`);
    console.log(`selectedInstrument: ${selectedInstrument}`);
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
        setInstruments(res.data.instruments);
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
                {Number(item.initial_units) > 0 ? "Long" : "Short"}
              </div>
              <div className="col">
                {item.is_active && "Pending signal"}
                {!item.is_active && Number(item.units) > 0 && "Open Trade"}
                {Number(item.units) == 0 && "Inactive"}
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
              defaultValue=""
              className={styles.input}
              onChange={handleChange}
            >
              <option value="" disabled selected>
                Select a strategy
              </option>
              {strategyDropdownList &&
                strategyDropdownList.map((item) => (
                  <option id={item.id}>{item.name}</option>
                ))}
            </select>
          </div>
        </div>
        <div className="col">
          <div className={`row ${styles.inputWrapper}`}>
            <select
              name="instrument"
              id="instrument"
              defaultValue=""
              className={styles.input}
              onChange={handleChange}
            >
              <option value="" disabled selected>
                Select an instrument
              </option>
              {instruments &&
                instruments.map((item) => (
                  <option id={item.name}>{item.display_name}</option>
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
    </div>
  );
};

export default RunStrategies;
