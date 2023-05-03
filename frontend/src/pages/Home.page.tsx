import React from "react";

import Fullscreen from "../components/Fullscreen.component";

const Home = () => {
  return (
    <Fullscreen>
      <div className="hero min-h-screen bg-base-200">
        <div className="text-center hero-content">
          <div className="max-w-md">
            <h1 className="mb-5 text-5xl font-bold overpass">
              Bell on a Budget
            </h1>
            <p className="mb-5">
              Find the cheapest Taco Bell near you - all with the click of a
              button.
            </p>
            <button className="btn btn-primary">Get Started</button>
          </div>
        </div>
      </div>
    </Fullscreen>
  );
};

export default Home;
