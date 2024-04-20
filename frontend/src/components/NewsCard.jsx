import React from "react";
import styles from "./NewsCard.module.css";
import Image from "./Image";

const NewsCard = (props) => {
  return (
    <div className={`col-sm-6`}>
      <div className={`card my-2 ${styles.card}`}>
        <Image
          src={props.image_url}
          className="card-img-top"
          alt={props.title}
        />
        <div className="card-body">
          <h5 className="card-title">{props.title}</h5>
          <p>
            <em>{props.source}</em>
          </p>
          <p className="card-text">
            {props.description && props.description.length > 500
              ? props.description.slice(0, 500).concat("...")
              : props.description}
          </p>
          {props.link && (
            <a
              href={props.link}
              target="_blank"
              className={`card-link ${styles.cardLink}`}
            >
              {props.link}
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsCard;
