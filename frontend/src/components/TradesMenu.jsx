import React, { useState } from "react";
import styles from "./TradesMenu.module.css";
import TradesNavbar from "./TradesNavbar";
import History from "./History";
import AccountSummary from "./AccountSummary";
import Position from "./Position";
import RunStrategies from "./RunStrategies";

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
      {active === "positions" && <Position />}
      {active === "summary" && <AccountSummary />}
      {active === "history" && <History />}
      {active === "strategies" && <RunStrategies />}
    </>
  );
};

export default TradesMenu;
