import { useState, useEffect } from "react";
import { apiClient } from "../api/client";

export function ClipsPage({ onLogout }) {
  const [text, setText] = useState("");
  const [clips, setClips] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    fetchClips();
  }, []);

  const fetchClips = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getClips();
      setClips(data.clips || []);
      setError("");
    } catch (err) {
      if (err.message === "Unauthorized") {
        onLogout();
      } else {
        setError("Failed to load clips");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveClip = async () => {
    if (!text.trim()) return;

    setIsSaving(true);
    try {
      await apiClient.createClip(text);
      setText("");
      await fetchClips();
      setError("");
    } catch (err) {
      if (err.message === "Unauthorized") {
        onLogout();
      } else {
        setError("Failed to save clip");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopyClip = async (clipText, clipId) => {
    try {
      await navigator.clipboard.writeText(clipText);
      setCopiedId(clipId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      setError("Failed to copy to clipboard");
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      onLogout();
    } catch (err) {
      setError("Failed to logout");
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const truncateText = (str, length = 60) => {
    return str.length > length ? str.substring(0, length) + "..." : str;
  };

  return (
    <div className="min-h-screen bg-xc-bg flex flex-col">
      {/* Header */}
      <header className="bg-xc-fill border-b-2 border-xc-brown p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-xc-brown">XClipboard</h1>
        <button onClick={handleLogout} className="btn-secondary">
          Logout
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col md:flex-row gap-4 p-4 max-w-6xl mx-auto w-full">
        {/* Textarea Section */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex-1 container-box flex flex-col">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste or type your text here..."
              className="flex-1 resize-none focus:outline-none bg-xc-fill text-xc-brown placeholder-xc-brown placeholder-opacity-60"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row">
            <button
              onClick={handleSaveClip}
              disabled={!text.trim() || isSaving}
              className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? "Saving..." : "Save Clip"}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-100 border-2 border-red-400 text-red-800">
              {error}
            </div>
          )}
        </div>

        {/* Clips Drawer */}
        <div className="md:w-80 flex flex-col">
          <div className="container-box flex-1 flex flex-col overflow-hidden">
            <h2 className="font-bold text-lg text-xc-brown mb-3">
              Recent Clips
            </h2>
            <div className="flex-1 overflow-y-auto space-y-2">
              {isLoading ? (
                <p className="text-xc-brown opacity-60">Loading...</p>
              ) : clips.length === 0 ? (
                <p className="text-xc-brown opacity-60">No clips yet</p>
              ) : (
                clips.map((clip) => (
                  <div
                    key={clip.clip_id}
                    className="p-2 bg-xc-bg rounded border border-xc-brown"
                  >
                    <div className="flex justify-between items-start gap-2 mb-1">
                      <span className="text-xs text-xc-brown opacity-70">
                        {formatTime(clip.created_at)}
                      </span>
                      <button
                        onClick={() =>
                          handleCopyClip(clip.clip_text, clip.clip_id)
                        }
                        className={`text-xs px-2 py-1 rounded transition-colors ${
                          copiedId === clip.clip_id
                            ? "bg-xc-brown text-xc-fill"
                            : "bg-xc-brown text-xc-fill hover:opacity-80"
                        }`}
                      >
                        {copiedId === clip.clip_id ? "✓" : "Copy"}
                      </button>
                    </div>
                    <p className="text-sm text-xc-brown break-words">
                      {truncateText(clip.clip_text)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
