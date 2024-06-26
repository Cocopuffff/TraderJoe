import React, { useEffect, useState } from "react";
import styles from "./SideList.module.css";
import ListItem from "./ListItem";
import Spinner from "./Spinner";
import AddRoundedIcon from "@mui/icons-material/AddRounded";

const SideList = (props) => {
  const [selectedItemId, setSelectedItemId] = useState("");
  const liftDelete = (id) => {
    props.handleDelete(id);
    if (selectedItemId === id) {
      setSelectedItemId("");
    }
  };

  const liftAdd = (event) => {
    props.handleAdd(event);
  };

  const handleSelect = (id) => {
    setSelectedItemId(id);
    props.handleSelectItem(id);
  };

  useEffect(() => {
    if (props.selectedItem && props.selectedItem.id) {
      setSelectedItemId(props.selectedItem.id);
    }
  }, [props.selectedItem]);

  return (
    <div className={`container-fluid ${styles.sideList}`}>
      <div className={`${styles.header}`}>
        <div>
          <h6>{props.title}</h6>
        </div>
        <button onClick={liftAdd} className={`${styles.add}`}>
          <AddRoundedIcon />
        </button>
      </div>
      {props?.watchlist?.map((item, idx) => {
        let priceChange;
        if (props.priceChanges) {
          const priceChangeObj = props.priceChanges.find(
            (instrument) => instrument.instrument === item.name
          );
          if (priceChangeObj) {
            priceChange = priceChangeObj.priceChange;
          }
        }
        return (
          <ListItem
            key={idx}
            id={item.id}
            name={item.name}
            displayName={item.display_name}
            onDelete={liftDelete}
            onSelect={handleSelect}
            selectedId={selectedItemId}
            addItem={props.addItem}
            priceChange={priceChange}
          />
        );
      })}
      {!props.watchlist && <Spinner />}
    </div>
  );
};

export default SideList;
