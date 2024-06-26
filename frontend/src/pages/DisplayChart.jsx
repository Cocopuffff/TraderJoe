import React, { useState } from "react";
import Chart from "../components/Chart";
import TradesMenu from "../components/TradesMenu";
import WatchList from "../components/WatchList";
import AddInstrumentsModal from "../components/AddInstrumentsModal";

const DisplayChart = (props) => {
  const [addInstrument, setAddInstrument] = useState(false);
  const [selectedInstrument, setSelectedInstrument] = useState("");
  const [newInstrument, setNewInstrument] = useState("");
  const [instrumentsWatchlist, setInstrumentsWatchlist] = useState(null);
  const [viewTrades, setViewTrades] = useState(false);

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
      <div className="displayChartVertical">
        {!viewTrades && (
          <Chart
            count="300"
            from=""
            to=""
            granularity={props.selectedTimeFrame}
            addInstrument={addInstrument}
            setAddInstrument={setAddInstrument}
            selectedInstrument={selectedInstrument}
            setSelectedInstrument={setSelectedInstrument}
            viewTrades={viewTrades}
          />
        )}
        <TradesMenu viewTrades={viewTrades} setViewTrades={setViewTrades} />
      </div>

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
