import React, { useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFaceSadTear } from "@fortawesome/free-solid-svg-icons";

import styles from "./styles/NotFound.module.css";

const NotFound = () => {
  useEffect(() => {
    document.title = `404 Not Found`;
  }, []);

  return (
    <>
      <div className="not-found page-content">
        <div className="content-wrapper">
          <div className={`${styles["notfound-container"]}`}>
            <div className={`${styles["notfound-message"]}`}>
              <div className={`${styles["notfound-title"]}`}>
                Oops! <FontAwesomeIcon icon={faFaceSadTear} />
              </div>
              <div className={`${styles["message"]}`}>
                <p>We can't seem to find the page you're looking for.</p>
                <br />
                <p>The requested URL</p>
                <p>"{window.location.href}"</p>
                <p>was not found on this server.</p>
              </div>
              <a href="/" className={`${styles["not-found-link"]}`}>
                Go back to the home page
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default NotFound;
