import React, { useState, useEffect, useContext } from "react";
import ErrorContext from "../context/ErrorContext";
import SideList from "./SideList";

const TopicList = (props) => {
  const [topics, setTopics] = useState([]);
  const ErrorCtx = useContext(ErrorContext);

  const getTopics = async (signal) => {
    try {
      const res = await fetch(import.meta.env.VITE_AIRTABLE_TOPICS, {
        signal,
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setTopics(data);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.log(error.message);
        ErrorCtx.setIsError(true);
        ErrorCtx.setErrorMessage(error.message);
      }
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    getTopics(controller.signal);

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    let controller;
    if (props.selectedTopic && !props.addTopic) {
      controller = new AbortController();
      getTopics(controller.signal);
    }
    return () => {
      if (controller) {
        controller.abort();
      }
    };
  }, [props.selectedTopic]);

  useEffect(() => {
    if (props.newSearchedTopic) {
      const newTopics = structuredClone(topics);
      newTopics.records.push(props.newSearchedTopic);
      setTopics(newTopics);
    }
  }, [props.newSearchedTopic]);

  const deleteTopic = async (id) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_AIRTABLE_TOPICS}/${id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${import.meta.env.VITE_AIRTABLE_APIKEY}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        const filteredTopics = topics.records.filter(
          (record) => record.id !== id
        );
        setTopics({ records: filteredTopics });
      }
    } catch (error) {
      console.log(error.message);
    }
  };
  const handleDelete = (id) => {
    deleteTopic(id);
  };

  const handleAdd = (event) => {
    props.setAddTopic(true);
  };

  const handleSelect = (id) => {
    const selectedTopic = topics.records.filter(
      (record) => record.id === id
    )[0];
    props.setSelectedTopic(selectedTopic);
  };

  return (
    <>
      <SideList
        records={topics}
        title="Topics"
        handleDelete={handleDelete}
        handleAdd={handleAdd}
        handleSelectItem={handleSelect}
        addItem={props.addTopic}
        selectedItem={props.selectedTopic}
      />
    </>
  );
};

export default TopicList;
