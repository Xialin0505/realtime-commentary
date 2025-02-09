import React, { useState } from 'react';

const PostAndStreamComponent = () => {
  const [input, setInput] = useState('');
  const [streamData, setStreamData] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePostAndStream = async () => {
    setLoading(true);
    setStreamData('');  // Clear previous data

    try {
      const response = await fetch('http://localhost:8000/api/upload_screenshot/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.body) {
        throw new Error('ReadableStream not supported in this browser.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value || new Uint8Array());
        setStreamData(prevData => prevData + chunk);
      }

    } catch (error) {
      console.error('Error:', error);
      setStreamData('An error occurred while streaming the response.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">POST and Stream Response</h2>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter your message"
        className="border p-2 rounded w-full mb-4"
      />
      <button
        onClick={handlePostAndStream}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {loading ? 'Processing...' : 'Submit and Stream'}
      </button>

      <div className="mt-4 bg-gray-100 p-4 rounded">
        <h3 className="font-semibold">Streaming Output:</h3>
        <pre>{streamData}</pre>
      </div>
    </div>
  );
};

export default PostAndStreamComponent;
