/**
 * SaveFileButton.jsx
 * "Download" on desktop (a plain link the server streams), "Save" via the share sheet on phones
 */

import { useState, useRef } from "react";
import { apiClient } from "../api/client";
import {
  prefersShareSheet,
  fetchClipFile,
  shareOrDownload,
} from "../utils/saveFile";

export function SaveFileButton({
  clipId,
  file,
  preparedFile = null,
  onError,
  className,
}) {
  const [state, setState] = useState("idle"); // idle | preparing | ready
  const fetchedFile = useRef(null);

  if (!prefersShareSheet()) {
    return (
      <a
        href={apiClient.fileUrl(clipId)}
        download={file.name}
        className={className}
      >
        Download
      </a>
    );
  }

  const handleClick = async () => {
    const ready = preparedFile || fetchedFile.current;
    if (ready) {
      // Already in memory, so the share sheet opens within this tap
      await shareOrDownload(ready, { allowRetry: false });
      setState("idle");
      return;
    }

    setState("preparing");
    try {
      fetchedFile.current = await fetchClipFile(clipId, file);
    } catch (err) {
      setState("idle");
      onError?.(err.message);
      return;
    }
    const result = await shareOrDownload(fetchedFile.current);
    setState(result === "needs-tap" ? "ready" : "idle");
  };

  return (
    <button
      onClick={handleClick}
      disabled={state === "preparing"}
      className={`${className} disabled:opacity-50`}
    >
      {state === "preparing" ? "..." : state === "ready" ? "Tap to save" : "Save"}
    </button>
  );
}
