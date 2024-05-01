import React, { useState, useRef, useEffect, useContext } from "react";
import styles from "./styles/ManageStrategy.module.css";
import useFetch from "../hooks/useFetch";
import AppContext from "../context/AppContext";
import Strategy from "../components/Strategy";
import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import ClearIcon from "@mui/icons-material/Clear";

const ManageStrategy = () => {
  const fetchData = useFetch();
  const [strategies, setStrategies] = useState([]);
  const [strategyTypes, setStrategyTypes] = useState([]);
  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [comments, setComments] = useState("");
  const [file, setFile] = useState(null);
  const [addStrategy, setAddStrategy] = useState(false);
  const appCtx = useContext(AppContext);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleChange = (event) => {
    switch (event.target.id) {
      case "name":
        setName(event.target.value);
        break;
      case "type":
        setType(event.currentTarget.value);
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

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      if (!name || !type || !comments || !file) {
        appCtx.setErrorMessage("all fields are required");
        appCtx.setIsError(true);
        return;
      }

      const formData = new FormData();
      formData.append("name", name);
      formData.append("type", type);
      formData.append("comments", comments);
      formData.append("file", file);

      const res = await fetch(
        import.meta.env.VITE_SERVER + "/api/strategy/create/",
        {
          method: "PUT",
          headers: {
            Authorization: "Bearer " + appCtx.accessToken,
          },
          body: formData,
        }
      );

      const data = await res.json();

      if (res.ok) {
        setName("");
        setType("");
        setComments("");
        setFile(null);
        fileInputRef.current.value = "";
        setAddStrategy(false);
        getStrategiesByUser();
      }
    } catch (error) {
      console.log(error);
      appCtx.setErrorMessage(error);
      appCtx.setIsError(true);
    }
  };

  const getStrategiesByUser = async () => {
    try {
      const res = await fetchData(
        "/api/strategy/",
        "GET",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        setStrategies(res.data.strategies);
      }
    } catch (error) {
      console.log(error);
      appCtx.setErrorMessage(error);
      appCtx.setIsError(true);
    }
  };

  const getStrategyTypes = async () => {
    try {
      const res = await fetchData(
        "/api/strategy/types/",
        "GET",
        undefined,
        appCtx.accessToken
      );

      if (res.ok) {
        setStrategyTypes(res.data.types);
      }
    } catch (error) {
      console.log(error);
      appCtx.setErrorMessage(error);
      appCtx.setIsError(true);
    }
  };

  useEffect(() => {
    getStrategiesByUser();
    getStrategyTypes();
  }, []);

  return (
    <div className={`container ${styles.review}`}>
      <div className={`row ${styles.table}`}>
        <div className={`row ${styles.tableheader}`}>
          <div className="col-md-1">Strategy Owner</div>
          <div className="col-md-2">Strategy Name</div>
          <div className="col-md-2">Type</div>
          <div className="col-md-3">Comments</div>
          <div className="col-md-3">Python script</div>
          <div className="col-md-1">Actions</div>
        </div>
        {strategies &&
          strategies.map((item) => {
            return (
              <Strategy
                item={item}
                key={item.id}
                handleChange={getStrategiesByUser}
                strategyTypes={strategyTypes}
              />
            );
          })}
        {!addStrategy && (
          <div className={`row ${styles.rows}`}>
            <div className="col-md-1" id={appCtx.id}></div>
            <div className="col-md-2"></div>
            <div className="col-md-2"></div>
            <div className="col-md-3"></div>
            <div className="col-md-3"></div>
            <div className="col-md-1 d-flex flex-column align-items-center">
              <button
                onClick={() => setAddStrategy(true)}
                className={styles.buttonGood}
              >
                <AddIcon />
              </button>
            </div>
          </div>
        )}
        {addStrategy && (
          <div className={`row ${styles.rows}`}>
            <div className="col-md-1" id={appCtx.id}></div>
            <div className="col-md-2">
              <div className="row">
                <input
                  className={styles.input}
                  id="name"
                  value={name}
                  onChange={handleChange}
                ></input>
              </div>
            </div>
            <div className="col-md-2">
              <select
                className={styles.input}
                id="type"
                value={type}
                onChange={handleChange}
              >
                {strategyTypes &&
                  strategyTypes.map((item, idx) => (
                    <option key={idx} value={item}>
                      {item}
                    </option>
                  ))}
              </select>
            </div>

            <textarea
              className={`col-md-3 ${styles.input}`}
              id="comments"
              value={comments}
              onChange={handleChange}
            ></textarea>
            <input
              className="col-md-3"
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".py"
            ></input>
            <div className="col-md-1 d-flex flex-column align-items-center">
              <button onClick={handleSubmit} className={styles.buttonGood}>
                <CheckIcon />
              </button>
              <button
                onClick={() => setAddStrategy(false)}
                className={styles.buttonGood}
              >
                <ClearIcon />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ManageStrategy;
