import React, { useRef, useEffect } from 'react';
import axios from 'axios';
import { Card } from 'primereact/card';

const VideoPlayer = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

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

        axios.post('http://localhost:8000/api/upload_screenshot/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }).catch(error => console.error('Error uploading screenshot:', error));
      }, 'image/png');
    }
  };

  return (
    <div className="p-4 grid gap-4">
      <Card className="shadow-lg rounded-2xl">
          <h2 className="text-xl font-bold mb-2">Local Video Playback with Screenshots</h2>
          <video ref={videoRef} width="640" height="360" controls crossOrigin="anonymous">
            <source src="http://localhost:8000/media/video/test.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
      </Card>
    </div>
  );
};

export default VideoPlayer;