import React, { useRef, useEffect, useState } from 'react';
import { Card } from 'primereact/card';
import FloatingWindow from "./floatingChatWindow";

const VideoPlayer = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [streamResponse, setStreamResponse] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      captureScreenshot();
    }, 5000); // Capture every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const captureScreenshot = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video && canvas) {
      const context = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'screenshot.png');

        fetch('http://localhost:8000/api/upload_screenshot/', {
          method: 'POST',
          body: formData,
        })
          .then(response => handleStream(response.body))
          .catch(error => console.error('Error uploading screenshot:', error));
      }, 'image/png');
    }
  };

  const handleStream = async (stream) => {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let done = false;

    setStreamResponse([]);  // Clear previous streamed data

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      const chunk = decoder.decode(value || new Uint8Array());
      setStreamResponse((prev) => [...prev, chunk]);  // Append streamed data
    }
  };

  return (
    <div className="p-4 grid gap-4">
      <Card className="shadow-lg rounded-2xl">
          <h2 className="text-xl font-bold mb-2">Local Video Playback with Screenshots</h2>
          
          <video ref={videoRef} width="70%" height="500" controls crossOrigin="anonymous">
            <source src="http://localhost:8000/media/video/test.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          
          <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
      
          <div className="mt-4 bg-gray-100 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Streaming Response:</h3>
            <pre className="whitespace-pre-wrap">{streamResponse || 'Waiting for response...'}</pre>
          </div>
      </Card>
      <FloatingWindow />
    </div>
  );
};

export default VideoPlayer;