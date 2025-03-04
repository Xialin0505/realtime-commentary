import React, { useState, useEffect } from "react";
import { Launcher } from "react-chat-window";

const FloatingWindow = ({ streamResponses }) => {
  const [messageList, setMessageList] = useState([
        {
            author: "them",
            type: "text",
            data: { text: "Waiting for Response..." }
        }
    ]);

  const _onMessageWasSent = (message) => {
    setMessageList((prev) => [...prev, message]);
  };

  const _sendMessage = (text) => {
    if (text.length > 0) {
      setMessageList((prev) => [
        ...prev,
        {
          author: "them",
          type: "text",
          data: { text },
        },
      ]);
    }
  };

  useEffect(() => {
    if (streamResponses && streamResponses.length > 0) {
      const newMessage = streamResponses[streamResponses.length - 1];
      console.log(newMessage)
      _sendMessage(newMessage);
    }
  }, [streamResponses]);

  return (
    <div>
      <Launcher
        agentProfile={{
          teamName: "Real-time Commentary",
          imageUrl: "/chatgpt.png",
        }}
        onMessageWasSent={_onMessageWasSent}
        messageList={messageList}
        showEmoji
      />
    </div>
  );
};

export default FloatingWindow;
