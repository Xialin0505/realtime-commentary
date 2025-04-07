import React, { useRef, useEffect, useState, useCallback } from "react";
import { Card } from "primereact/card";
import FloatingWindow from "./floatingChatWindow";

// Timestamp Formatter 1: seconds -> HH:MM:SS.MS
function formatTimestamp(seconds) {
  const totalSeconds = Math.floor(seconds);
  const hrs = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  const msecs = Math.floor((seconds - Math.floor(seconds)) * 1000);
  const pad2 = (n) => String(n).padStart(2, "0");
  const pad3 = (n) => String(n).padStart(3, "0");
  return `${pad2(hrs)}:${pad2(mins)}:${pad2(secs)}.${pad3(msecs)}`;
}

// Timestamp Parser 2: HH:MM:SS.MS -> seconds
function parseTimestamp(formatted) {
  try {
    const [hh, mm, rest] = formatted.split(":");
    const [ss, ms] = rest.split(".");
    return (
      parseInt(hh) * 3600000 +
      parseInt(mm) * 60000 +
      parseInt(ss) * 1000 +
      parseInt(ms)
    );
  } catch (e) {
    console.warn("Failed to parse timestamp:", formatted);
    return 0;
  }
}

// Debounce Helper: debounce the function call
function debounce(fn, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}

// Video Player Component
const VideoPlayer = ({ userInput }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [videoSource, setVideoSource] = useState("");
  const [websocketId, setWebsocketId] = useState("");
  const [error, setError] = useState(null);

  const [commentaryHistory, setCommentaryHistory] = useState([]);
  const [messageHistory, setMessageHistory] = useState([]);
  const commentariesRef = useRef([]);
  const commentaryBufferRef = useRef([]);

  const cleanHistory = useCallback(() => {
    commentariesRef.current = [];
    commentaryBufferRef.current = [];
    setCommentaryHistory([]);
    setMessageHistory([]);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
    wsRef.current = null;
  }, []);

  // Process Commentary Helper: binary search to find the insert index
  const findInsertIndex = (timestamp) => {
    const parsedNew = parseTimestamp(timestamp);
    let low = 0, high = commentariesRef.current.length;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (parseTimestamp(commentariesRef.current[mid].timestamp) < parsedNew) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    return low;
  };

  class AudioQueue {
    constructor() {
        this.queue = [];
        this.playing = false;
    }

    enqueue(base64Audio) {
        this.queue.push(base64Audio);
        this.playNext();
    }

    async playNext() {
        if (this.playing || this.queue.length === 0) return;

        this.playing = true;
        const base64 = this.queue.shift();
        const audio = new Audio("data:audio/wav;base64," + base64);

        await new Promise((resolve) => {
            audio.onended = resolve;
            audio.onerror = resolve;
            audio.play().catch(resolve); // Handle autoplay errors silently
        });

        this.playing = false;
        this.playNext(); // Play the next one
    }
}

  // Process Commentary: insert the new commentary into the commentary history
  const processCommentary = useCallback((timestamp, content) => {
    const index = findInsertIndex(timestamp);
    const parsedNew = parseTimestamp(timestamp);
  
    // append if exists
    if ( index < commentariesRef.current.length && parseTimestamp(commentariesRef.current[index].timestamp) === parsedNew) {
      commentariesRef.current[index].content += content;
      console.log(`${new Date().toISOString()} [DEBUG] Appended commentary: ${commentariesRef.current[index].content}`);
    // insert if not exists
    } else {
      commentariesRef.current.splice(index, 0, {
        timestamp,
        content,
      });
      console.log(`${new Date().toISOString()} [DEBUG] Insert new commentary: ${commentariesRef.current[index].content}`);
    }
    setCommentaryHistory(commentariesRef.current.map((c) => `[${c.timestamp}] ${c.content}`));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (commentaryBufferRef.current.length > 0) {
        const next = commentaryBufferRef.current.shift();
        processCommentary(next.timestamp, next.content);
      }
    }, 500);
  
    return () => clearInterval(interval);
  }, [processCommentary]);

  // URL Parser: parse the user input and set the video source and websocket id
  useEffect(() => {
    cleanHistory();

    if (!userInput) {
      setError(null);
      setVideoSource("http://localhost:8000/media/video/test.mp4");
      setWebsocketId("test");
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
      return;
    }

    setError("Invalid video ID or URL.");
  }, [userInput]);

  // WebSocket Connection and Message Handler
  useEffect(() => {
    if (!websocketId) return;

    const socket = new WebSocket(`ws://localhost:8000/ws/commentary/${websocketId}/`);
    wsRef.current = socket;
    const audioQueue = new AudioQueue();

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "commentary") {
          commentaryBufferRef.current.push({timestamp: message.timestamp, content: message.content});
          if (message.audio) {
            audioQueue.enqueue(message.audio);
          }
        } else if (message.type === "chat") {
          setMessageHistory((prev) => [...prev, message.content]);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    socket.onopen = () => console.log("WebSocket connected.");
    socket.onclose = () => console.log("WebSocket disconnected.");
    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => {
      socket.close();
      wsRef.current = null;
    };
  }, [websocketId, processCommentary]);

  // Capture Screenshot: capture the screenshot of the current frame and send it to the backend
  const captureScreenshot = useCallback(debounce(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ws = wsRef.current;
    if (!video || video.paused || video.ended || !canvas || !ws || ws.readyState !== WebSocket.OPEN) return;

    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const videoTime = formatTimestamp(video.currentTime);

    canvas.toBlob((blob) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        try {
          ws.send(JSON.stringify({
            type: "screenshot",
            image: reader.result,
            timestamp: videoTime,
          }));
          console.log("Sent screenshot to backend:", videoTime);
        } catch (e) {
          console.error("Failed to send WebSocket message:", e);
        }
      };
      reader.readAsDataURL(blob);
    }, 'image/png');
  }, 300), []);

  // Capture Screenshot Timer
  useEffect(() => {
    const interval = setInterval(() => {
      captureScreenshot();
    }, 500);
    return () => clearInterval(interval);
  }, [captureScreenshot]);

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  // Web Renderer
  return (
    <div className="p-4 grid gap-4">
      <Card className="shadow-lg rounded-2xl">
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