import React, { useState, useEffect, useContext } from "react";
import AppContext from "../context/AppContext";
import SideList from "./SideList";
import useFetch from "../hooks/useFetch";

const WatchList = (props) => {
  const [instruments, setInstruments] = useState([]);
  const [priceChanges, setPriceChanges] = useState([]);
  const appCtx = useContext(AppContext);
  const fetchData = useFetch();

  const getInstruments = async () => {
    try {
      const res = await fetchData(
        "/api/watchlist/",
        "POST",
        { id: appCtx.id },
        appCtx.accessToken
      );

      if (res.ok) {
        setInstruments(res.data.watchlist);
        if (!props.selectedInstrument) {
          props.setSelectedInstrument(res.data.watchlist[0]);
        }
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setIsError(true);
      appCtx.setErrorMessage(error.message);
    }
  };

  const getPriceChangeForTheDay = async (signal) => {
    try {
      if (props.instrumentsWatchlist.length === 0) {
        return;
      }
      const requiredInstruments = props.instrumentsWatchlist.join(":D:M%2C");
      let url = `${import.meta.env.VITE_FXPRACTICE_OANDA}/v3/accounts/${
        import.meta.env.VITE_OANDA_ACCOUNT
      }/candles/latest?candleSpecifications=${requiredInstruments}:D:M`;

      const res = await fetch(url, {
        signal,
        headers: {
          Authorization: "Bearer " + import.meta.env.VITE_OANDA_DEMO_API_KEY,
          Connection: "Keep-Alive",
        },
      });

      if (res.ok) {
        const data = await res.json();
        const temp = [];
        for (const inst of data.latestCandles) {
          const priceClose = parseFloat(
            inst.candles[inst.candles.length - 1].mid.c
          );
          const pricePreviousClose = parseFloat(
            inst.candles[inst.candles.length - 2].mid.c
          );
          const priceChangePercentage =
            (priceClose / pricePreviousClose - 1) * 100;
          const newInst = {
            instrument: inst.instrument,
            priceChange: priceChangePercentage,
          };
          temp.push(newInst);
        }
        setPriceChanges(temp);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.log(error.message);
        ErrorCtx.setIsError(true);
        ErrorCtx.setErrorMessage(error.message);
      }
    }
  };

  useEffect(() => {
    getInstruments();
  }, []);

  useEffect(() => {
    if (props.newInstrument) {
      const temp = structuredClone(instruments);
      temp.push(props.newInstrument);
      setInstruments(temp);
    }
  }, [props.newInstrument]);

  useEffect(() => {
    if (instruments) {
      const temp = structuredClone(instruments).map((record) => {
        return record.name;
      });
      props.setInstrumentsWatchlist(temp);
    }
  }, [instruments]);

  useEffect(() => {
    const controller = new AbortController();
    if (props.instrumentsWatchlist) {
      getPriceChangeForTheDay(controller.signal);
    }
    return () => {
      controller.abort();
    };
  }, [props.instrumentsWatchlist]);

  const deleteInstrument = async (id) => {
    try {
      const res = await fetchData(
        `/api/watchlist/${id}/`,
        "DELETE",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        const filteredInstruments = instruments.filter(
          (record) => record.id != id
        );
        setInstruments(filteredInstruments);
      }
    } catch (error) {
      console.log(error.message);
    }
  };
  const handleDelete = (id) => {
    deleteInstrument(id);
  };

  const handleAdd = (event) => {
    props.setAddInstrument(true);
  };

  const handleSelect = (id) => {
    const selectedInstrument = instruments.watchlist.filter(
      (record) => record.id === id
    )[0];
    props.setSelectedInstrument(selectedInstrument);
  };

  return (
    <>
      <SideList
        watchlist={instruments}
        title="Watchlist"
        handleDelete={handleDelete}
        handleAdd={handleAdd}
        handleSelectItem={handleSelect}
        addItem={props.addInstrument}
        selectedItem={props.selectedInstrument}
        priceChanges={priceChanges}
      />
    </>
  );
};

export default WatchList;
