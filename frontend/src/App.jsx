import React, { Suspense, useContext, useState } from "react";
import AppContext from "./context/AppContext";
import ErrorModal from "./components/ErrorModal";
import { Route, Routes } from "react-router-dom";
import Loader from "./components/Loader";
import Navbar from "./components/Navbar";
import "./App.css";

const HomePage = React.lazy(() => import("./pages/HomePage"));
const Login = React.lazy(() => import("./pages/Login"));
const Register = React.lazy(() => import("./pages/Register"));
const ManageStrategy = React.lazy(() => import("./pages/ManageStrategy"));
const ReviewTraders = React.lazy(() => import("./pages/ReviewTraders"));
const DisplayChart = React.lazy(() => import("./pages/DisplayChart"));
const NotFound = React.lazy(() => import("./pages/NotFound"));

const availableTimeFrames = [
  { name: "S5", displayName: "5 seconds", displayShort: "5s" },
  { name: "S10", displayName: "10 seconds", displayShort: "10s" },
  { name: "S15", displayName: "15 seconds", displayShort: "15s" },
  { name: "S30", displayName: "30 seconds", displayShort: "30s" },
  { name: "M1", displayName: "1 minute", displayShort: "1m" },
  { name: "M2", displayName: "2 minutes", displayShort: "2m" },
  { name: "M4", displayName: "4 minutes", displayShort: "4m" },
  { name: "M5", displayName: "5 minutes", displayShort: "5m" },
  { name: "M10", displayName: "10 minutes", displayShort: "10m" },
  { name: "M15", displayName: "15 minutes", displayShort: "15m" },
  { name: "M30", displayName: "30 minutes", displayShort: "30m" },
  { name: "H1", displayName: "1 hour", displayShort: "1h" },
  { name: "H2", displayName: "2 hours", displayShort: "2h" },
  { name: "H3", displayName: "3 hours", displayShort: "3h" },
  { name: "H4", displayName: "4 hours", displayShort: "4h" },
  { name: "H6", displayName: "6 hours", displayShort: "6h" },
  { name: "H8", displayName: "8 hours", displayShort: "8h" },
  { name: "H12", displayName: "12 hours", displayShort: "12h" },
  { name: "D", displayName: "1 day", displayShort: "1D" },
  { name: "W", displayName: "1 week", displayShort: "1W" },
  { name: "M", displayName: "1 month", displayShort: "1M" },
];

function App() {
  const [timeFrames, setTimeFrames] = useState(availableTimeFrames);
  const [selectedTimeFrame, setSelectedTimeFrame] = useState({
    name: "D",
    displayName: "1 day",
    displayShort: "1D",
  });
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [role, setRole] = useState("");
  const [id, setId] = useState("");
  const [email, setEmail] = useState("");
  const [expirationDate, setExpirationDate] = useState("");
  const [showLogin, setShowLogin] = useState(true);

  const handleDismiss = () => {
    setIsError(false);
  };

  const logOut = () => {
    setExpirationDate("");
    setAccessToken("");
    setRole("");
    setId("");
    setEmail("");
    if (localStorage.getItem("refreshToken")) {
      localStorage.removeItem("refreshToken");
    }
  };

  return (
    <Suspense fallback={<Loader />}>
      <AppContext.Provider
        value={{
          isError,
          setIsError,
          errorMessage,
          setErrorMessage,
          accessToken,
          setAccessToken,
          role,
          setRole,
          id,
          setId,
          expirationDate,
          setExpirationDate,
          showLogin,
          setShowLogin,
          email,
          setEmail,
          logOut,
        }}
      >
        <Navbar
          selectedTimeFrame={selectedTimeFrame}
          setSelectedTimeFrame={setSelectedTimeFrame}
          timeFrames={timeFrames}
        />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="review" element={<ReviewTraders />} />
          <Route path="strategies" element={<ManageStrategy />} />
          <Route
            path="chart"
            element={
              <DisplayChart selectedTimeFrame={selectedTimeFrame.name} />
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
        {isError && (
          <ErrorModal
            title="Oops, something went wrong"
            message={errorMessage}
            okayClicked={handleDismiss}
          />
        )}
      </AppContext.Provider>
    </Suspense>
  );
}

export default App;
