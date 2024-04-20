import React, { useEffect, useState, useRef, useContext } from "react";
import Spinner from "./Spinner";
import SummarySentiment from "./SummarySentiment";
import NewsCard from "./NewsCard";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPenToSquare,
  faSearch,
  faX,
  faCheck,
  faFaceSadTear,
} from "@fortawesome/free-solid-svg-icons";
import styles from "./TopicFeed.module.css";
import ErrorContext from "../context/ErrorContext";

const TopicFeed = (props) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const inputRef = useRef();
  const nameRef = useRef();
  const searchParamRef = useRef();
  const ErrorCtx = useContext(ErrorContext);

  const getData = async (signal) => {
    if (
      props.selectedTopic &&
      props.selectedTopic.fields &&
      props.selectedTopic.fields.searchParameter
    ) {
      try {
        setIsLoading(true);
        let encodedSearchParameter = encodeURIComponent(
          props.selectedTopic.fields.searchParameter
        );
        const res = await fetch(
          `https://newsdata.io/api/1/news?apikey=pub_395314400f4a938c352dab00d456c0c590114&q=${encodedSearchParameter}&language=en&category=business,top,world`,
          { signal }
        );
        // const res = await fetch(new Request("newsdata.json"), { signal });

        if (res.ok) {
          let data = await res.json();
          data = JSON.stringify(data);
          setIsLoading(false);
          setData(data);
        }
      } catch (error) {
        if (error.name != "AbortError") {
          console.log(error.message);
          setIsLoading(false);
          ErrorCtx.setIsError(true);
          ErrorCtx.setErrorMessage(error.message);
        }
      }
    }
  };

  const createTopic = async (newTopic) => {
    try {
      const res = await fetch(import.meta.env.VITE_AIRTABLE_TOPICS, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
        },
        body: JSON.stringify(newTopic),
      });

      if (res.ok) {
        const data = await res.json();
        props.setSelectedTopic(data);
        props.passNewTopicToTopicList(data);
      }
    } catch (error) {
      console.log(error.message);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    getData(controller.signal);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    inputRef.current.value = "";
    const controller = new AbortController();
    getData(controller.signal);
    return () => controller.abort();
  }, [props.selectedTopic]);

  useEffect(() => {
    if (props.addTopic) {
      inputRef.current.focus();
    }
  }, [props.addTopic]);

  const handleSearch = () => {
    if (inputRef.current.value !== "") {
      const newTopic = {
        fields: {
          searchParameter: inputRef.current.value,
          displayName: inputRef.current.value.split(" ")[0],
        },
      };
      createTopic(newTopic);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSearch();
      inputRef.current.value = "";
    }
  };

  const toggleEdit = () => {
    setEditing(!editing);
  };

  const handleEdit = async () => {
    const temp = structuredClone(props.selectedTopic);
    temp.fields.searchParameter = searchParamRef.current.value;
    temp.fields.displayName = nameRef.current.value;
    delete temp.createdTime;
    try {
      const res = await fetch(import.meta.env.VITE_AIRTABLE_TOPICS, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ records: [temp] }),
      });

      if (res.ok) {
        const data = await res.json();
        props.setSelectedTopic(temp);
        setEditing(false);
      }
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <div className={`container-fluid px-5 ${styles.topicFeed}`}>
      <div className={`row d-flex justify-content-center`}>
        <div
          className={`${styles.searchBar} ${
            props.addTopic ? `${styles.selected}` : ""
          }`}
        >
          <input
            type="text"
            className={`${styles.searchInput}`}
            placeholder="Search topics to follow"
            onFocus={() => props.setAddTopic(true)}
            onBlur={() => props.setAddTopic(false)}
            onKeyDown={handleKeyDown}
            ref={inputRef}
          />
          <button className={`${styles.searchButton}`} onClick={handleSearch}>
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
      </div>
      {props.selectedTopic && (
        <div className={styles.topic}>
          <div className={styles.searchTopic}>
            {editing ? (
              <input
                type="text"
                defaultValue={props.selectedTopic.fields.displayName}
                placeholder="Name"
                className={`${styles.modify}`}
                ref={nameRef}
              ></input>
            ) : (
              <h4>{props.selectedTopic.fields.displayName}</h4>
            )}
          </div>
          <div className={styles.searchParameter}>
            {editing ? (
              <input
                type="text"
                defaultValue={props.selectedTopic.fields.searchParameter}
                placeholder="Search parameter"
                className={`${styles.modify}`}
                ref={searchParamRef}
              ></input>
            ) : (
              ""
            )}
          </div>
          <div>
            {editing ? (
              <button className={styles.edit} onClick={toggleEdit}>
                <FontAwesomeIcon icon={faX} />
              </button>
            ) : (
              ""
            )}
            {editing ? (
              <button className={styles.edit} onClick={handleEdit}>
                <FontAwesomeIcon
                  icon={faCheck}
                  className={`${styles.active}`}
                />
              </button>
            ) : (
              <button className={styles.edit} onClick={toggleEdit}>
                <FontAwesomeIcon icon={faPenToSquare} />
              </button>
            )}
          </div>
        </div>
      )}
      {isLoading ? (
        <Spinner />
      ) : (
        <>
          {data && JSON.parse(data).results.length === 0 ? (
            <div className={styles["notfound-container"]}>
              <div className={`${styles["notfound-title"]}`}>
                Oops! <FontAwesomeIcon icon={faFaceSadTear} />
              </div>
              <div className={`${styles["message"]}`}>
                <p>No results found.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="row">
                {data && (
                  <SummarySentiment data={data} topic={props.selectedTopic} />
                )}
              </div>
              {data && (
                <div className="row">
                  <h5>News Feed</h5>
                </div>
              )}
              <div className="row">
                {data &&
                  JSON.parse(data).results.length !== 0 &&
                  JSON.parse(data).results.map((result, idx) => {
                    return (
                      <NewsCard
                        key={idx}
                        image_url={result.image_url}
                        source={result.source_url}
                        title={result.title}
                        description={result.description}
                        link={result.link}
                      />
                    );
                  })}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default TopicFeed;
