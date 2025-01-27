import './App.css';

import React, { useEffect, useState, useRef } from "react";

const App = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Socket connection
  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws/commentary/"); // only init once

    socketRef.current.onopen = () => {
      console.log("WebSocket connected!");
    };

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, data.message]);
    };

    socketRef.current.onclose = () => {
      console.log("WebSocket disconnected.");
    };

    return () => {
      socketRef.current.close();
    };
  }, []);

  const sendMessage = () => {
    if (input.trim()) {
      socketRef.current.send(JSON.stringify({ message: input }));
      setInput("");
    }
  };

  // Scroll to bottom when new message comes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Page
  return (
    <div>
      <h1>WebSocket Chat</h1>
      <div
        style={{
          border: "1px solid black",
          padding: "10px",
          height: "200px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column"
        }}
      >
        {messages.map((msg, index) => (
          <p key={index} style={{ margin: "5px 0" }}>{msg}</p>
        ))}
        <div ref={messagesEndRef} /> {}
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        onKeyPress={(e) => e.key === "Enter" && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};

export default App;
