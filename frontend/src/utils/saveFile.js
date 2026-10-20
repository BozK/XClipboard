/**
 * saveFile.js
 * Getting a file onto a phone. iOS home-screen web apps can't download at all (a file link just
 * replaces the app's page), and even in Safari a download lands in Files instead of Photos.
 * The share sheet works in both, and offers "Save Image" / "Save to Files".
 */

import { apiClient } from "../api/client";

// Touch devices with file sharing get the share sheet; desktops keep normal downloads
export const prefersShareSheet = () =>
  window.matchMedia("(pointer: coarse)").matches &&
  typeof navigator.canShare === "function";

export async function fetchClipFile(clipId, file) {
  const response = await fetch(apiClient.fileUrl(clipId), {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(
      response.status === 401 ? "Unauthorized" : "Failed to fetch file",
    );
  }
  const blob = await response.blob();
  return new File([blob], file.name, { type: file.mime_type });
}

export function downloadFile(fileObj) {
  const url = URL.createObjectURL(fileObj);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileObj.name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

/**
 * Open the share sheet for an already-fetched File, falling back to a download.
 * Returns "done", or "needs-tap" when the tap that started it expired while the file was
 * fetching (Safari only allows sharing right after a tap), so the caller should ask for another.
 */
export async function shareOrDownload(fileObj, { allowRetry = true } = {}) {
  if (navigator.canShare?.({ files: [fileObj] })) {
    try {
      await navigator.share({ files: [fileObj] });
      return "done";
    } catch (err) {
      if (err.name === "AbortError") return "done"; // Closed the share sheet
      if (err.name === "NotAllowedError" && allowRetry) return "needs-tap";
    }
  }
  downloadFile(fileObj);
  return "done";
}
