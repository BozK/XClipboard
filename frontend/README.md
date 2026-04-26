# XClipboard Frontend

React frontend for XClipboard - a self-hosted text snippet sharing application.

## Quick Start

### Prerequisites

- Node.js 16+ and npm (or yarn)

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

This starts the Vite dev server at `http://localhost:5173`.

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Configuration

By default, the frontend expects the backend API at `http://localhost:8000`.

To customize the API URL, create a `.env.local` file:

```env
VITE_API_URL=http://your-backend-url:8000
```

## Stack

- **React 18** - UI framework
- **Vite** - Frontend build tool
- **Tailwind CSS** - Styling
- **Browser Clipboard API** - Copy to clipboard functionality

## Design

- **Colors**: Mint chocolate theme
  - Background green: #A8E4A0
  - Brown text/borders: #2f1801
  - Light fill: #eaffe7
- **Responsive**: Mobile-first design with desktop support
- **Simple UI**: Minimal, distraction-free interface

## Project Structure

```
src/
  ├── pages/
  │   ├── LoginPage.jsx      # Login form
  │   └── ClipsPage.jsx      # Main clip management page
  ├── api/
  │   └── client.js          # API client functions
  ├── App.jsx                # Main app component with auth state
  ├── main.jsx               # Entry point
  └── index.css              # Global styles & Tailwind setup
```

## Features

- User login with session authentication
- Create and save text snippets
- View 25 most recent clips with timestamps
- Copy clips to clipboard with one click
- Responsive design for mobile and desktop
