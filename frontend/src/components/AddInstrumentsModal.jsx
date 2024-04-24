import React, { useState, useEffect, useRef, useContext } from "react";
import ReactDOM from "react-dom";
import Spinner from "./Spinner";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPlus,
  faMagnifyingGlass,
  faCheckCircle,
} from "@fortawesome/free-solid-svg-icons";
import styles from "./AddInstrumentsModal.module.css";
import AppContext from "../context/AppContext";
import useFetch from "../hooks/useFetch";

const Overlay = (props) => {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState(null);
  const [filteredResult, setFilteredResult] = useState([]);
  const searchRef = useRef();
  const appCtx = useContext(AppContext);
  const fetchData = useFetch();

  const getInstruments = async (signal) => {
    try {
      const url = `
        ${import.meta.env.VITE_FXPRACTICE_OANDA}/v3/accounts/${
        import.meta.env.VITE_OANDA_ACCOUNT
      }/instruments`;
      setIsLoading(true);
      const res = await fetch(url, {
        signal,
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_OANDA_DEMO_API_KEY}`,
          Connection: "keep-alive",
        },
      });

      if (res.ok) {
        const data = await res.json();
        const sortedData = data.instruments
          .toSorted((a, b) => {
            const nameA = a.name.toUpperCase();
            const nameB = b.name.toUpperCase();
            if (nameA > nameB) {
              return 1;
            } else if (nameA < nameB) {
              return -1;
            } else {
              return 0;
            }
          })
          .toSorted((a, b) => {
            const typeA = a.type.toUpperCase();
            const typeB = b.type.toUpperCase();
            if (typeA > typeB) {
              return 1;
            } else if (typeA < typeB) {
              return -1;
            } else {
              return 0;
            }
          });
        setData(sortedData);
        setFilteredResult(sortedData);
        setIsLoading(false);
      }
    } catch (error) {
      console.log(error.message);
    }
  };

  const AddInstrumentToWatchlist = async (instrument) => {
    try {
      let new_item = {
        name: instrument.name,
        display_name: instrument.displayName,
        type: instrument.type,
      };

      const res = await fetchData(
        "/api/watchlist/add/",
        "PUT",
        new_item,
        appCtx.accessToken
      );

      if (res.ok) {
        props.handleAddInstrument(res.data.new_instrument);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    getInstruments(controller.signal);

    return () => {
      controller.abort();
    };
  }, []);

  const handleFilterName = (event) => {
    if (filteredResult && searchRef.current.value.length !== 0) {
      setFilteredResult(
        data.filter(
          (instrument) =>
            instrument.displayName
              .toUpperCase()
              .indexOf(searchRef.current.value.toUpperCase()) !== -1
        )
      );
    }
  };

  return (
    <div className={styles.backdrop} onClick={props.okayClick}>
      <div
        className={`${styles.board} ${styles.modal}`}
        onClick={(event) => event.stopPropagation()}
      >
        <header className={styles.header}>
          <h2>{props.title}</h2>
        </header>
        <div className={styles.searchRow}>
          <label htmlFor="search">
            <FontAwesomeIcon
              icon={faMagnifyingGlass}
              className={styles.searchIcon}
            />
          </label>
          <input
            className={`${styles.search}`}
            type="text"
            placeholder="Search"
            id="search"
            onChange={handleFilterName}
            ref={searchRef}
          ></input>
        </div>

        <div className={`row ${styles.subheader}`}>
          <div className="col-sm-5 d-flex">Name</div>
          <div className="col-sm-5">Type</div>
          <div className="col-sm-2"></div>
        </div>
        <div className={styles.content}>
          {isLoading ? (
            <Spinner />
          ) : (
            <>
              {filteredResult &&
                filteredResult.map((instrument, idx) => {
                  return (
                    <div
                      className={`row ${styles.instrument}`}
                      key={idx}
                      id={instrument.name}
                    >
                      <div className="col-sm-5">{instrument.displayName}</div>
                      <div className="col-sm-5">{instrument.type}</div>
                      <div className="col-sm-2">
                        {(!props.instrumentsWatchlist ||
                          !props.instrumentsWatchlist.includes(
                            instrument.name
                          )) && (
                          <button
                            onClick={() => AddInstrumentToWatchlist(instrument)}
                            className={`${styles.add}`}
                          >
                            <FontAwesomeIcon icon={faPlus} />
                          </button>
                        )}
                        {props.instrumentsWatchlist &&
                          props.instrumentsWatchlist.includes(
                            instrument.name
                          ) && (
                            <button className={`${styles.added}`}>
                              <FontAwesomeIcon icon={faCheckCircle} />
                            </button>
                          )}
                      </div>
                    </div>
                  );
                })}
            </>
          )}
        </div>
        <footer className={styles.actions}>
          <button onClick={props.okayClick} className="btn btn-primary">
            Cancel
          </button>
        </footer>
      </div>
    </div>
  );
};

const AddInstrumentsModal = (props) => {
  return (
    <>
      {ReactDOM.createPortal(
        <Overlay
          title={props.title}
          handleAddInstrument={props.handleAddInstrument}
          okayClick={props.handleOkay}
          instrumentsWatchlist={props.instrumentsWatchlist}
        />,
        document.querySelector("#modal-root")
      )}
    </>
  );
};

export default AddInstrumentsModal;
