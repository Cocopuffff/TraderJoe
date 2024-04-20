import React, { useState, useEffect, useContext } from "react";
import ErrorContext from "../context/ErrorContext";
import SideList from "./SideList";

const WatchList = (props) => {
  const [instruments, setInstruments] = useState([]);
  const [priceChanges, setPriceChanges] = useState([]);
  const ErrorCtx = useContext(ErrorContext);

  const getInstruments = async (signal) => {
    try {
      const res = await fetch(import.meta.env.VITE_AIRTABLE_WATCHLIST, {
        signal,
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setInstruments(data);
        if (!props.selectedInstrument) {
          props.setSelectedInstrument(data.records[0]);
        }
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.log(error.message);
        ErrorCtx.setIsError(true);
        ErrorCtx.setErrorMessage(error.message);
      }
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
        console.log(temp);
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
    const controller = new AbortController();
    getInstruments(controller.signal);
    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    if (props.newInstrument) {
      const temp = structuredClone(instruments);
      temp.records.push(props.newInstrument);
      setInstruments(temp);
    }
  }, [props.newInstrument]);

  useEffect(() => {
    if (instruments.records) {
      const temp = structuredClone(instruments.records).map((record) => {
        return record.fields.name;
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
      const res = await fetch(
        `${import.meta.env.VITE_AIRTABLE_WATCHLIST}/${id}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
          },
        }
      );

      if (res.ok) {
        const data = await res.json();
        const filteredInstruments = instruments.records.filter(
          (record) => record.id !== id
        );
        setInstruments({ records: filteredInstruments });
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
    const selectedInstrument = instruments.records.filter(
      (record) => record.id === id
    )[0];
    props.setSelectedInstrument(selectedInstrument);
  };

  return (
    <>
      <SideList
        records={instruments}
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
