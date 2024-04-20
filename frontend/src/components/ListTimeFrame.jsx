import React, { useState, useEffect } from "react";
import styles from "./ListTimeFrame.module.css";

const ListTimeFrame = (props) => {
  const [isHover, setIsHover] = useState(false);
  const [isActive, setIsActive] = useState(false);

  const handleClick = () => {
    props.setSelectedTimeFrame(props.timeFrame);
  };

  useEffect(() => {
    if (props.selectedTimeFrame.name === props.timeFrame.name) {
      setIsActive(true);
    } else {
      setIsActive(false);
    }
  }, [props.selectedTimeFrame]);

  return (
    <button
      id={props.timeFrame.name}
      className={`${styles.timeFrame} ${
        isActive || isHover ? styles.active : ""
      }`}
      onMouseEnter={() => setIsHover(true)}
      onMouseLeave={() => setIsHover(false)}
      onClick={handleClick}
    >
      {props.timeFrame.displayShort}
    </button>
  );
};

export default ListTimeFrame;
