/**
 * ImageViewer.jsx
 * Full-size image overlay. Stays on the page, so home-screen web apps (which have no back
 * button) never get stranded on a bare image URL
 */

import { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import { prefersShareSheet, fetchClipFile } from "../utils/saveFile";
import { SaveFileButton } from "./SaveFileButton";

export function ImageViewer({ clipId, file, onClose, onError }) {
  // Show the thumbnail right away, then swap in the full image once it loads
  const [src, setSrc] = useState(apiClient.thumbUrl(clipId));
  const [preparedFile, setPreparedFile] = useState(null);

  useEffect(() => {
    const handleKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    if (!prefersShareSheet()) {
      setSrc(apiClient.fileUrl(clipId, true));
      return;
    }

    // On phones, fetch the file once and use it for both display and Save, so the share sheet
    // can open the moment Save is tapped
    let objectUrl = null;
    let cancelled = false;
    fetchClipFile(clipId, file)
      .then((fetched) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(fetched);
        setSrc(objectUrl);
        setPreparedFile(fetched);
      })
      .catch((err) => !cancelled && onError?.(err.message));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [clipId]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/85 flex flex-col"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={file.name}
    >
      <div
        className="flex items-center justify-between gap-2 p-2 text-white"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="truncate text-sm">{file.name}</span>
        <div className="flex gap-2 shrink-0">
          <SaveFileButton
            clipId={clipId}
            file={file}
            preparedFile={preparedFile}
            onError={onError}
            className="text-sm px-3 py-1 rounded bg-xc-fill text-xc-brown hover:opacity-80"
          />
          <button
            onClick={onClose}
            className="text-sm px-3 py-1 rounded border border-white hover:bg-white/20"
          >
            Close
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0 flex items-center justify-center p-2">
        <img
          src={src}
          alt={file.name}
          onClick={(e) => e.stopPropagation()}
          // Browsers other than Safari can't show HEIC: keep the thumbnail
          onError={() => setSrc(apiClient.thumbUrl(clipId))}
          className="max-w-full max-h-full object-contain"
        />
      </div>
    </div>
  );
}
