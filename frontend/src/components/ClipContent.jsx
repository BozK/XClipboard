/**
 * ClipContent.jsx
 * Renders clip text with auto-detected and linkified URLs
 * Intelligently handles text before, after, and between URLs
 */

export function ClipContent({ text, maxLength = 60 }) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);

  // Truncate helper for URLs that might be very long
  const truncateUrl = (url, length = 40) => {
    return url.length > length ? url.substring(0, length) + "..." : url;
  };

  return (
    <span className="break-words">
      {parts.map((part, i) =>
        urlRegex.test(part) ? (
          <a
            key={i}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline hover:opacity-70 transition-opacity"
          >
            {truncateUrl(part)}
          </a>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </span>
  );
}
