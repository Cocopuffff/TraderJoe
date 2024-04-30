import React, { useState, useRef, useContext, useEffect } from "react";
import AppContext from "../context/AppContext";
import styles from "./Strategy.module.css";
import EditIcon from "@mui/icons-material/Edit";
import ClearIcon from "@mui/icons-material/Clear";
import UndoIcon from "@mui/icons-material/Undo";
import CheckIcon from "@mui/icons-material/Check";
import useFetch from "../hooks/useFetch";

const Strategy = (props) => {
  const appCtx = useContext(AppContext);
  const [isEdit, setIsEdit] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [comments, setComments] = useState("");
  const [file, setFile] = useState(null);
  const fetchData = useFetch();

  const handleChange = (event) => {
    switch (event.target.id) {
      case "name":
        setName(event.target.value);
        break;
      case "type":
        setType(event.target.value);
        break;
      case "comments":
        setComments(event.target.value);
        break;
      default:
        console.error(
          `something went wrong in parsing changes: ${event.target.id}`
        );
    }
  };

  const handleFileChange = (event) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleDelete = async (event) => {
    try {
      const res = await fetchData(
        "/api/strategy/",
        "DELETE",
        { id: event.currentTarget.id },
        appCtx.accessToken
      );

      if (res.ok) {
        props.handleChange();
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data);
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  const handleUpdate = async (event) => {
    try {
      const formData = new FormData();
      formData.append("id", props.item.id);
      formData.append("type", type);
      formData.append("name", name);
      formData.append("comments", comments);
      if (file) {
        formData.append("file", file);
      }

      const res = await fetch(import.meta.env.VITE_SERVER + "/api/strategy/", {
        method: "PATCH",
        headers: {
          Authorization: "Bearer " + appCtx.accessToken,
        },
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setIsEdit(false);
        props.handleChange();
      } else {
        console.log(res.data);
        appCtx.setErrorMessage(res.data || "Error updating strategy");
        appCtx.setIsError(true);
      }
    } catch (error) {
      console.log(error.message);
      appCtx.setErrorMessage(error.message);
      appCtx.setIsError(true);
    }
  };

  useEffect(() => {
    if (props) {
      setName(props.item.name);
      setType(props.item.type);
      setComments(props.item.comments);
    }
  }, []);

  return (
    <div className={`row ${styles.rows}`}>
      <div className="col-md-1 text-center">
        {props.item.owner_id === appCtx.id ? "You" : "Not you"}
      </div>
      {!isEdit && (
        <>
          <div className="col-md-2 text-center">{props.item.name}</div>
          <div className="col-md-2 text-center">{props.item.type}</div>
          <div className="col-md-3">{props.item.comments}</div>
          <div className="col-md-3 text-center">
            {props.item.script_path.split("/")[1]}
          </div>
        </>
      )}
      {isEdit && (
        <>
          <input
            className={`col-md-2 ${styles.input}`}
            id="name"
            value={name}
            onChange={handleChange}
          />
          <select
            className={`col-md-2 ${styles.input}`}
            id="type"
            value={type}
            onChange={handleChange}
          >
            {props.strategyTypes &&
              props.strategyTypes.map((item, idx) => (
                <option key={idx} value={item}>
                  {item}
                </option>
              ))}
          </select>
          <textarea
            className={`col-md-3 ${styles.input}`}
            id="comments"
            value={comments}
            onChange={handleChange}
          />
          <div className="col-md-3 d-flex flex-column">
            {file === null ? (
              ""
            ) : (
              <div>{`Current: ${props.item.script_path.split("/")[1]}`}</div>
            )}
            <input
              type="file"
              id="file"
              onChange={handleFileChange}
              accept=".py"
            />
          </div>
        </>
      )}
      <div className="col-md-1 d-flex flex-column align-items-center">
        {!isEdit && (
          <button
            id={props.item.id}
            onClick={() => setIsEdit(!isEdit)}
            className={styles.buttonGood}
          >
            <EditIcon />
          </button>
        )}
        {isEdit && (
          <button
            id={props.item.id}
            onClick={() => setIsEdit(!isEdit)}
            className={styles.buttonGood}
          >
            <UndoIcon />
          </button>
        )}
        {!isEdit && (
          <button
            id={props.item.id}
            onClick={handleDelete}
            className={styles.buttonBad}
          >
            <ClearIcon />
          </button>
        )}
        {isEdit && (
          <button
            id={props.item.id}
            onClick={handleUpdate}
            className={styles.buttonGood}
          >
            <CheckIcon />
          </button>
        )}
      </div>
    </div>
  );
};

export default Strategy;
