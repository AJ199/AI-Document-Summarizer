import React, { useState } from "react";

const API =
  import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== ""
    ? import.meta.env.VITE_API_URL
    : "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [docId, setDocId] = useState("");
  const [question, setQuestion] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus("Uploading and extracting...");
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/upload`, {
      method: "POST",
      body: form,
    });
    const data = await res.json();
    if (data.doc_id) {
      setDocId(data.doc_id);
      setStatus(`Uploaded. ${data.chunks} chunks indexed.`);
    } else {
      setStatus("Upload failed.");
    }
    setLoading(false);
  };

  const handleSummarize = async () => {
    if (!docId) return;
    setLoading(true);
    setStatus("Summarizing via Azure OpenAI...");
    const res = await fetch(`${API}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_id: docId,
        question: question || null,
      }),
    });
    const data = await res.json();
    setSummary(data.summary || "No summary returned.");
    setLoading(false);
    setStatus("Done.");
  };

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "system-ui" }}>
      <h1>AI Document Summarizer</h1>
      <p>Upload a PDF/Doc → extract → RAG → summarize with citations.</p>

      {/* Upload */}
      <div
        style={{
          border: "2px dashed #ccc",
          padding: 16,
          borderRadius: 8,
          marginBottom: 12,
        }}
      >
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
        />
        <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: 8 }}>
          Upload
        </button>
      </div>

      {/* Question */}
      {docId && (
        <div style={{ marginBottom: 12 }}>
          <label>Ask a question (optional): </label>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            style={{ width: "60%", marginRight: 8 }}
            placeholder="e.g. Summarize methods section..."
          />
          <button onClick={handleSummarize} disabled={loading}>
            Summarize
          </button>
        </div>
      )}

      {status && <p><b>Status:</b> {status}</p>}
      {loading && <p>Working...</p>}

      {/* Summary */}
      {summary && (
        <div style={{ marginTop: 20 }}>
          <h3>Summary</h3>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              background: "#f4f4f4",
              padding: 12,
              borderRadius: 6,
            }}
          >
            {summary}
          </pre>
        </div>
      )}
    </div>
  );
}
