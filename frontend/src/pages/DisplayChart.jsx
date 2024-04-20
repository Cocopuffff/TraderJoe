import React, { useState } from "react";
import Chart from "../components/Chart";
import WatchList from "../components/WatchList";
import AddInstrumentsModal from "../components/AddInstrumentsModal";

const DisplayChart = (props) => {
  const [addInstrument, setAddInstrument] = useState(false);
  const [selectedInstrument, setSelectedInstrument] = useState("");
  const [newInstrument, setNewInstrument] = useState("");
  const [instrumentsWatchlist, setInstrumentsWatchlist] = useState(null);

  const passInstrument = (instrument) => {
    setNewInstrument(instrument);
  };

  const cancelAddInstrument = () => {
    setAddInstrument(!addInstrument);
  };

  return (
    <div className="displayView">
      {addInstrument && (
        <AddInstrumentsModal
          title="Add instruments to your watchlist"
          handleAddInstrument={passInstrument}
          handleOkay={cancelAddInstrument}
          instrumentsWatchlist={instrumentsWatchlist}
        />
      )}
      <Chart
        count="300"
        from=""
        to=""
        granularity={props.selectedTimeFrame}
        addInstrument={addInstrument}
        setAddInstrument={setAddInstrument}
        selectedInstrument={selectedInstrument}
        setSelectedInstrument={setSelectedInstrument}
      />
      <WatchList
        addInstrument={addInstrument}
        setAddInstrument={setAddInstrument}
        selectedInstrument={selectedInstrument}
        setSelectedInstrument={setSelectedInstrument}
        newInstrument={newInstrument}
        instrumentsWatchlist={instrumentsWatchlist}
        setInstrumentsWatchlist={setInstrumentsWatchlist}
      />
    </div>
  );
};

export default DisplayChart;
