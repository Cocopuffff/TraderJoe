import React, { useState } from "react";
import TopicFeed from "../components/TopicFeed";
import TopicList from "../components/TopicList";

const DisplayNews = () => {
  const [addTopic, setAddTopic] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [newSearchedTopic, setNewSearchedTopic] = useState("");

  const passNewTopicToTopicList = (topic) => {
    setNewSearchedTopic(topic);
  };

  return (
    <div className="displayView">
      <TopicFeed
        addTopic={addTopic}
        setAddTopic={setAddTopic}
        selectedTopic={selectedTopic}
        setSelectedTopic={setSelectedTopic}
        passNewTopicToTopicList={passNewTopicToTopicList}
      />
      <TopicList
        addTopic={addTopic}
        setAddTopic={setAddTopic}
        selectedTopic={selectedTopic}
        setSelectedTopic={setSelectedTopic}
        newSearchedTopic={newSearchedTopic}
      />
    </div>
  );
};

export default DisplayNews;
