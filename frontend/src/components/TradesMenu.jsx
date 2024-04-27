import React, { useState } from "react";
import styles from "./TradesMenu.module.css";
import TradesNavbar from "./TradesNavbar";
import History from "./History";
import AccountSummary from "./AccountSummary";

const TradesMenu = (props) => {
  const [active, setActive] = useState(null);

  return (
    <>
      <TradesNavbar
        viewTrades={props.viewTrades}
        setViewTrades={props.setViewTrades}
        active={active}
        setActive={setActive}
      />
      {active === "positions" && <div>position</div>}
      {active === "summary" && <AccountSummary />}
      {active === "history" && <History />}
      {active === "strategies" && <div>strategies</div>}
    </>
  );
};

export default TradesMenu;
