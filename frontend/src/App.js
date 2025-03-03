import React from "react";
import VideoPlayer from "./pages/getVideoFromBackend";
import Header from "./pages/header";
import Footer from "./pages/footer";

const App = () => {
  // Page
  return (
    <div>
      <Header />
      <main >
        <VideoPlayer />
      </main>
      <Footer />
    </div>
  );
};

export default App;
