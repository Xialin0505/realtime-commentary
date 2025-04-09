import React from "react";

export default function TTSSelector({ ttsMode, setTTSMode }) {
  const options = [
    {
      value: "browser",
      label: "Browser TTS",
      desc: "Fast, runs locally in your browser",
    },
    {
      value: "backend",
      label: "Self-deployed TTS",
      desc: "Higher quality audio, but may have some delay",
    },
  ];

  const isLocked = ttsMode !== ""; // once selected, lock it

  return (
    <div className="my-4">
      <h3 className="font-semibold text-lg mb-2">🔊 Select Audio Source</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((opt) => (
          <label
            key={opt.value}
            className={`border rounded-xl p-4 cursor-pointer transition-all ${
              ttsMode === opt.value
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 hover:border-gray-400"
            } ${isLocked && ttsMode !== opt.value ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <input
                type="radio"
                name="tts-mode"
                value={opt.value}
                checked={ttsMode === opt.value}
                onChange={() => {
                  if (!isLocked) setTTSMode(opt.value);
                }}
                disabled={isLocked}
                className="accent-blue-500"
              />
              <span className="text-base font-medium">{opt.label}</span>
            </div>
            <p className="text-sm text-gray-400">{opt.desc}</p>
          </label>
        ))}
      </div>
    </div>
  );
}
