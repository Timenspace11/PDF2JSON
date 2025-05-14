// src/UploadForm.tsx
import React, { useState, ChangeEvent, FormEvent } from "react";

const UploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Handle file selection
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Handle file upload and receive JSON result from the backend
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Error uploading file");
      }

      const jsonData = await response.json();
      setResult(jsonData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Create a download link for the JSON data and simulate a click to download the file
  const handleDownload = () => {
    if (result) {
      const dataStr = JSON.stringify(result, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "result.json";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto" }}>
      <h2>Upload a File</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".jpg, .jpeg, .png, .pdf"
          onChange={handleFileChange}
        />
        <button type="submit" disabled={loading || !selectedFile}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {result && (
        <div>
          <h3>Result:</h3>
          <pre
            style={{
              textAlign: "left",
              background: "#f0f0f0",
              padding: "1rem",
              overflowX: "auto",
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
          <button onClick={handleDownload}>Download JSON</button>
        </div>
      )}
    </div>
  );
};

export default UploadForm;
