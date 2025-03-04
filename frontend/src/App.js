import React, { useState } from "react";
import VideoPlayer from "./pages/getVideoFromBackend";
import Header from "./pages/header";
import Footer from "./pages/footer";

const App = () => {
  const [videoInput, setVideoInput] = useState("");
  const [submittedInput, setSubmittedInput] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    setSubmittedInput(videoInput.trim() || "test");
  };

  return (
    <div className="p-4">
      <Header />
      <main >
        <h1 className="text-2xl font-bold mb-4">Live Sports Commentary</h1>

        <form onSubmit={handleSubmit} className="mb-4">
          <input
            type="text"
            value={videoInput}
            onChange={(e) => setVideoInput(e.target.value)}
            placeholder="Enter video ID or full video URL ('test' by default)"
            className="border p-2 rounded mr-2"
          />
          <button type="submit" className="bg-blue-500 text-white p-2 rounded">
            Load Video
          </button>
        </form>

        <VideoPlayer userInput={submittedInput} />
      </main>
      <Footer />
    </div>
  );
};

export default App;
