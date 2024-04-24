import React, { useEffect, useState, useContext, useRef } from "react";
import styles from "./ListItem.module.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faX } from "@fortawesome/free-solid-svg-icons";
import ClearIcon from "@mui/icons-material/Clear";

const ListItem = (props) => {
  const [isActive, setActive] = useState(false);
  const [isHover, setHover] = useState(false);
  const [isButtonHover, setButtonHover] = useState(false);
  const buttonRef = useRef();

  const handleButtonClick = (event) => {
    props.onDelete(event.currentTarget.parentNode.id);
  };

  const handleItemClick = (event) => {
    if (buttonRef.current && !buttonRef.current.contains(event.target)) {
      setActive(true);
      props.onSelect(props.id);
    }
  };

  const evaluateSelection = (id) => {
    if (id !== props.id) {
      setActive(false);
    }
    if (id === props.id) {
      setActive(true);
    }
  };

  useEffect(() => {
    setActive(false);
  }, [props.addItem]);

  useEffect(() => {
    evaluateSelection(props.selectedId);
  }, [props.selectedId]);

  return (
    <div
      className={`row align-items-center ${styles["sidebarItem"]} ${
        isActive ? `${styles.selected}` : ""
      }`}
      id={props.id}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={handleItemClick}
    >
      <div className={`${styles.name} col-6`}>{props.displayName}</div>
      {props.priceChange && (
        <div
          className={`col-4 ${styles.priceChange} ${
            props.priceChange >= 0 ? styles.upColour : styles.downColour
          }`}
        >
          {props.priceChange.toFixed(2) + "%"}
        </div>
      )}
      <button
        className={`col-1 ${styles.delete}  ${
          isHover ? "" : `${styles.hidden}`
        } ${isButtonHover ? `${styles.active}` : ""}`}
        ref={buttonRef}
        onClick={handleButtonClick}
        onMouseEnter={() => setButtonHover(true)}
        onMouseLeave={() => setButtonHover(false)}
      >
        <ClearIcon />
      </button>
    </div>
  );
};

export default ListItem;
