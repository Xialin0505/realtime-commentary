export default function useBrowserTTS() {
    const speak = (text) => {
      if (!window.speechSynthesis) {
        console.error("SpeechSynthesis not supported on this browser.");
        return;
      }
  
      const utterance = new SpeechSynthesisUtterance(text);
  
      utterance.lang = 'en-US';
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;
  
      window.speechSynthesis.speak(utterance);
    };
  
    return { speak };
  }
  