import React, { useState, useRef, useEffect } from "react";
import JolPlayer from "jol-player";
import { FileUpload } from 'primereact/fileupload';
import { Panel } from "primereact/panel";
import { Skeleton } from "primereact/skeleton";
import { Divider } from 'primereact/divider';
import { Chip } from 'primereact/chip';

const RealtimeCommentary = () => {
    const [videoSrc, setVideoSrc] = useState("");
    const socketRef = useRef(null);
    const [comment, setComment] = useState(""); 

    useEffect(() => {
        socketRef.current = new WebSocket("ws://localhost:8000/ws/commentary/");
    
        socketRef.current.onopen = () => {
            console.log("WebSocket connected!");
        };
        socketRef.current.onmessage = (event) => {
          const newComment = event.data;
          setComment(newComment);
        };
    
         return () => {
          if (socketRef.current) {
            socketRef.current.close();
          }
        };
    }, []);
  
  const handleFileChange = (event) => {
    const file = event.files[0];
    socketRef.current.send(JSON.stringify({ message: file }));
    // note that react must use http to send file to django, to be implemented

    if (file) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
    }
  };

  const onPlay = (val) => {
        socketRef.current.send(JSON.stringify({ message: val }));
    };

  return (
    <>
        <Panel header='Select a video'>
            <FileUpload 
                mode="basic" 
                name="demo[]" 
                url="/api/upload" 
                accept="video/*" 
                customUpload 
                uploadHandler={handleFileChange} 
            />
        </Panel>
        <Panel header='Video play and commentary'>
            {
                videoSrc ?
                (
                    <JolPlayer
                        onPlay={onPlay}
                        option={{
                            videoSrc: videoSrc,
                            width: 750,
                            height: 360,
                            // autoPlay: true,
                            isShowMultiple: false,
                            isProgressFloat: false,
                            isShowPauseButton: false,
                            isShowPicture: false,
                            isShowScreenshot: false,
                            isShowSet: false,
                            isShowWebFullScreen: false,
                            isToast: false,
                        }}
                    />
                )  :
                (
                    <Skeleton variant="rectangular" width={750} height={360} />
                )
            }
            <Divider />
            <Chip label="Commentary" />
            {
                comment ?
                <text>
                    {comment}
                </text> :
                <Skeleton width="75%"></Skeleton>
            }
        </Panel>
    </>
  );
}

export default RealtimeCommentary;
