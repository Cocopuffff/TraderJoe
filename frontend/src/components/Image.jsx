import React, { useEffect, useState } from "react";

const Image = (props) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleError = (event) => {
    setIsVisible(false);
  };

  useEffect(() => {
    if (!props.src) {
      handleError();
    }
  }, []);

  return (
    <div>
      {isVisible && (
        <img
          src={props.src}
          alt={props.alt}
          onError={handleError}
          className={props.className}
        />
      )}
    </div>
  );
};

export default Image;
