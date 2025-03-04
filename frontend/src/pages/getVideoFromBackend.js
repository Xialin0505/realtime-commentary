import React, { useRef, useEffect, useState } from "react";
import { Card } from "primereact/card";
import FloatingWindow from "./floatingChatWindow";

const VideoPlayer = ({ userInput }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [videoSource, setVideoSource] = useState("");
  const [websocketId, setWebsocketId] = useState("");
  const [error, setError] = useState(null);
  const [commentaryHistory, setCommentaryHistory] = useState([]);
  const [messageHistory, setMessageHistory] = useState([]);

  const cleanHistory = () => {
    setCommentaryHistory([]);
    setMessageHistory([]);
  };

  useEffect(() => {
    if (!userInput) {
      setError(null);
      setVideoSource("http://localhost:8000/media/video/test.mp4");
      setWebsocketId("test");
      cleanHistory();
      return;
    }

    const trimmedInput = userInput.trim();
    const isLikelyUrl = /^(https?:\/\/|www\.)/i.test(trimmedInput);

    if (isLikelyUrl) {
      try {
        const url = trimmedInput.startsWith("www.") ? `https://${trimmedInput}` : trimmedInput;
        new URL(url);
        setError(null);
        setVideoSource(url);
        setWebsocketId(url);
        cleanHistory();
      } catch {
        setError("Invalid URL format.");
      }
      return;
    }

    const isValidVideoId = /^[a-zA-Z0-9_-]+$/.test(trimmedInput);
    if (isValidVideoId) {
      const backendUrl = `http://localhost:8000/media/video/${trimmedInput}.mp4`;

      fetch(backendUrl, { method: "HEAD" })
        .then((response) => {
          if (response.ok) {
            setError(null);
            setVideoSource(backendUrl);
            setWebsocketId(trimmedInput);
          } else {
            setError("Backend video not found.");
          }
        })
        .catch(() => setError("Error checking backend video."));
      
      cleanHistory();
      return;
    }

    setError("Invalid video ID or URL.");
  }, [userInput]);

  useEffect(() => {
    if (!websocketId) return;

    console.log(`Resetting WebSocket for ${websocketId}`);

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    console.log(`Creating WebSocket connection for ${websocketId}`);
    const socket = new WebSocket(`ws://localhost:8000/ws/commentary/${websocketId}/`);

    socket.onopen = () => {
      console.log("WebSocket connected.");
      wsRef.current = socket;
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected.");
      wsRef.current = null;
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "commentary") {
        setCommentaryHistory((prev) => [...prev, message.content]);
      } else if (message.type === "chat") {
        setMessageHistory((prev) => [...prev, message.content]);
      }
    };

    return () => {
      console.log("Cleaning up WebSocket...");
      if (wsRef.current) {
        wsRef.current.close();
      }
      wsRef.current = null;
    };
  }, [websocketId]);

  useEffect(() => {
    const interval = setInterval(() => {
      captureScreenshot();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const captureScreenshot = () => {
    console.log("Processing screenshot capture.");
  
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ws = wsRef.current;
  
    console.log("Debug ws:", ws);
    console.log("Video status - paused:", video?.paused, "ended:", video?.ended, "readyState:", video?.readyState);
    
    if (!ws) {
      console.warn("Skipping captureScreenshot: WebSocket is null.");
      return;
    }
  
    if (ws.readyState !== WebSocket.OPEN) {
      console.warn("Skipping captureScreenshot: WebSocket is not open. readyState:", ws.readyState);
      return;
    }
  
    if (!video) {
      console.warn("Skipping captureScreenshot: Video element is null.");
      return;
    }
  
    if (video.paused) {
      console.warn("Skipping captureScreenshot: Video is paused.");
      return;
    }
  
    if (video.ended) {
      console.warn("Skipping captureScreenshot: Video has ended.");
      return;
    }
  
    if (!canvas) {
      console.warn("Skipping captureScreenshot: Canvas element is null.");
      return;
    }
  
    if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      console.warn("Skipping captureScreenshot: Video is not ready for playback. readyState:", video.readyState);
      return;
    }
  
    // Screenshot capture logic
    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
  
    // const imageBase64 = canvas.toDataURL("image/png").split(",")[1];
    // ws.send(JSON.stringify({ type: "screenshot", image: imageBase64 }));

    canvas.toBlob((blob) => {
      const reader = new FileReader();
      reader.readAsArrayBuffer(blob);
      reader.onloadend = () => {
          ws.send(reader.result);
      };
  }, 'image/png');
  
    console.log("Screenshot capture complete.");
  };
  
  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  return (
    <div className="p-4 grid gap-4">
      <Card className="shadow-lg rounded-2xl">
        {/* <h2 className="text-xl font-bold mb-2">Fencing Game Video</h2> */}

        <div className="relative">
          {error ? (
            <div className="w-3/4 h-[500px] bg-black flex items-center justify-center text-red-500">
              {error}
            </div>
          ) : (
            <video key={videoSource} ref={videoRef} width="70%" height="50%" controls crossOrigin="anonymous">
              <source src={videoSource} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          )}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
      </Card>

      <FloatingWindow key={userInput} streamResponses={commentaryHistory} />
    </div>
  );
};

export default VideoPlayer;
