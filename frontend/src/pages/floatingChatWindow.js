import React from "react";
import { Launcher } from "react-chat-window";

const FloatingWindow = ({ streamResponses }) => {
  const messageList =
    streamResponses && streamResponses.length > 0
      ? streamResponses.map((text) => ({
          author: "them",
          type: "text",
          data: { text },
        }))
      : [
          {
            author: "them",
            type: "text",
            data: { text: "Waiting for Response..." },
          },
        ];

  return (
    <Launcher
      agentProfile={{
        teamName: "Real-time Commentary",
        imageUrl: "/chatgpt.png",
      }}
      messageList={messageList}
      onMessageWasSent={() => {}}
      showEmoji
    />
  );
};

export default FloatingWindow;
