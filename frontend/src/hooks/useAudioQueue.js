import { useRef } from "react";

/**
 * Hook for handling async TTS fetch + orderly audio playback
 */
export default function useAudioQueue(ttsApiUrl) {
  const queueRef = useRef([]);
  const isPlayingRef = useRef(false);

  const _processQueue = async () => {
    if (isPlayingRef.current || queueRef.current.length === 0) return;

    isPlayingRef.current = true;
    const getAudioUrl = queueRef.current.shift();

    try {
      const audioUrl = await getAudioUrl();
      const audio = new Audio(audioUrl);

      await new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = resolve;
        audio.play().catch(resolve);
      });
    } catch (err) {
      console.error("Audio playback failed:", err);
    }

    isPlayingRef.current = false;
    _processQueue(); // process next
  };

  const enqueueSpeech = (text) => {
    const fetchAudio = async () => {
      try {
        const res = await fetch(ttsApiUrl, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "Connection": "keep-alive", // ✅ 让浏览器复用连接
         },
          body: JSON.stringify({ text })
        });

        if (!res.ok) {
          throw new Error(`TTS fetch failed: ${res.status}`);
        }
        console.log("Received audio")

        const blob = await res.blob();
        return URL.createObjectURL(blob);
      } catch (err) {
        console.error("TTS fetch error:", err);
        return null;
      }
    };

    queueRef.current.push(fetchAudio);
    _processQueue(); // try to start playing
  };

  return { enqueueSpeech };
}
