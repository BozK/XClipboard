/**
 * ClipFile.jsx
 * Renders a file clip: a tappable preview for images, or a name + size row for everything else
 */

import { apiClient } from "../api/client";

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export function ClipFile({ clipId, file, onOpen }) {
  if (file.has_thumb) {
    return (
      <button
        type="button"
        onClick={onOpen}
        title={file.name}
        className="block w-full"
      >
        {/* max-h keeps a portrait photo from filling a landscape phone screen */}
        <img
          src={apiClient.thumbUrl(clipId)}
          alt={file.name}
          loading="lazy"
          className="w-full max-h-48 object-contain rounded-sm bg-xc-fill"
        />
      </button>
    );
  }

  return (
    <span className="flex items-center gap-2 min-w-0">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-5 h-5 shrink-0"
        aria-hidden="true"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
      <span className="truncate" title={file.name}>
        {file.name}
      </span>
      <span className="text-xs opacity-70 shrink-0">
        {formatSize(file.size_bytes)}
      </span>
    </span>
  );
}
