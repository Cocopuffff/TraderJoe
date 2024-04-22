import React, { useState, useEffect } from "react";
import styles from "./styles/ReviewTraders.module.css";
import useFetch from "../hooks/useFetch";

const ReviewTraders = () => {
  const fetchData = useFetch();
  const [data, setData] = useState(null);

  const getData = async () => {
    try {
      const res = await fetchData("/auth/", "GET", undefined, undefined);
      if (res.ok) {
        setData(res.data);
      }
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    getData();
  }, []);

  return (
    <div>
      Review your traders here!
      <div>{JSON.stringify(data)}</div>
    </div>
  );
};

export default ReviewTraders;
